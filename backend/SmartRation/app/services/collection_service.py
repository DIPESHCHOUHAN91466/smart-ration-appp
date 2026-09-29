"""Confirming a ration collection at the counter.

Every check is re-run on the server (never trusting that nothing changed since the verification screen
was loaded); then stock is deducted, the token completed, the receipt and ledger rows written and the
action audited — in ONE transaction. If any item is short, nothing is issued (no partial issue, never a
negative balance). A client retry with the same idempotency key returns the original receipt.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound
from app.database.enums import InventoryMovementType, NotificationType, RationType, TokenStatus, UserRole, VerificationAction
from app.database.models import (
    Beneficiary,
    Family,
    FamilyMember,
    Inventory,
    RationCollection,
    RationCollectionItem,
    RationScheme,
    RationShop,
    Token,
    TokenItem,
    User,
)
from app.services import audit_service, entitlement_service, inventory_ledger, notification_service, verification_audit_service
from app.services.verification_service import READY, build_response
from app.utils.dotnet import num, ymd_hm
from app.utils.time import utc_now

log = logging.getLogger("smartration.collection")


def _receipt(code: str, token_number: str, beneficiary_name: str, family_size: int, scheme_code: str,
             items: Sequence[tuple[int, Decimal]], shop_name: str, collected_at: datetime) -> dict:
    return {"collectionCode": code, "tokenNumber": token_number, "beneficiaryName": beneficiary_name,
            "familySize": family_size, "schemeCode": scheme_code,
            "issuedItems": [{"rationType": RationType(t).name, "quantity": num(q)} for t, q in items],
            "totalQuantityKg": num(sum((q for _, q in items), start=Decimal(0))), "shopName": shop_name, "collectedAt": ymd_hm(collected_at)}


def _existing_receipt(db: Session, c: RationCollection) -> dict:
    token = db.get(Token, c.TokenId)
    beneficiary = db.get(Beneficiary, c.BeneficiaryId)
    user = db.get(User, beneficiary.UserId) if beneficiary else None
    family = db.get(Family, beneficiary.FamilyId) if beneficiary else None
    scheme = db.get(RationScheme, family.RationSchemeId) if family else None
    size = db.scalar(select(func.count()).select_from(FamilyMember).where(FamilyMember.FamilyId == family.Id)) if family else 0
    shop = db.get(RationShop, c.RationShopId)
    items = [(i.RationType, i.Quantity) for i in db.scalars(
        select(RationCollectionItem).where(RationCollectionItem.RationCollectionId == c.Id).order_by(RationCollectionItem.Id))]
    return _receipt(c.CollectionCode, token.TokenNumber if token else "", user.FullName if user else "", size or 0,
                    scheme.SchemeCode if scheme else "", items, shop.ShopName if shop else "", c.CollectedAt)


def _reject(db: Session, actor: Actor, method: str, token: Token, beneficiary_id: int, reason: str | None) -> None:
    verification_audit_service.log(db, actor, VerificationAction.CollectionRejected, "BLOCKED", method, token_number=token.TokenNumber,
                                   beneficiary_id=beneficiary_id, shop_id=token.RationShopId, reason=reason)
    db.commit()


def confirm(db: Session, actor: Actor, token_id: int, method: str, idempotency_key: str | None = None) -> dict:
    if idempotency_key:
        previous = db.scalar(select(RationCollection).where(RationCollection.IdempotencyKey == idempotency_key))
        if previous is not None:
            if previous.TokenId != token_id or previous.OperatorUserId != actor.user_id:
                raise Conflict("This request key was already used for a different collection.", "IDEMPOTENCY_KEY_REUSED")
            return _existing_receipt(db, previous)

    token = db.get(Token, token_id)
    if token is None:
        raise NotFound("Booking not found.")
    if actor.role == UserRole.ShopOwner and token.RationShopId != actor.ration_shop_id:
        raise Forbidden("This booking belongs to a different ration shop.")

    # The authoritative gate: Aadhaar / passbook / mobile / token / family / entitlement, re-checked now.
    verification = build_response(db, actor, token, method)
    beneficiary_id = verification["beneficiary"]["id"]
    summary = verification["verificationSummary"]
    if summary["overallStatus"] != READY:
        _reject(db, actor, method, token, beneficiary_id, summary["blockedReason"])
        raise Conflict(summary["blockedReason"] or "Collection is blocked.")

    requested = [i for i in db.scalars(select(TokenItem).where(TokenItem.TokenId == token.Id).order_by(TokenItem.Id)) if i.Quantity > 0]
    if not requested:
        raise BadRequest("This booking has no items to issue.", "NO_ITEMS")
    try:
        entitlement_service.ensure_request_within_entitlement(verification["entitlement"],
                                                              [(RationType(i.RationType), i.Quantity) for i in requested])
    except BadRequest as exc:
        _reject(db, actor, method, token, beneficiary_id, exc.message)
        raise

    # From here on everything is one transaction. The token and the shop's stock rows are locked so a
    # second counter can't issue the same token or the same last bag at the same moment.
    try:
        locked = db.scalar(select(Token).where(Token.Id == token_id).with_for_update())
        if locked is None or locked.Status != TokenStatus.Confirmed:
            raise Conflict("Could not complete the collection due to a concurrent update. Please try again.", "CONCURRENT_UPDATE")
        token = locked
        stock = {i.RationType: i for i in db.scalars(
            select(Inventory).where(Inventory.RationShopId == token.RationShopId).order_by(Inventory.Id).with_for_update())}
        short = next((i for i in requested if i.RationType not in stock or stock[i.RationType].AvailableQuantity < i.Quantity), None)
        if short is not None:
            db.rollback()
            name = RationType(short.RationType).name
            _reject(db, actor, method, token, beneficiary_id, f"Insufficient {name} stock.")
            raise Conflict(f"Insufficient {name} stock to complete this collection.", "INSUFFICIENT_STOCK")

        now = utc_now()
        for item in requested:
            inv = stock[item.RationType]
            inv.AvailableQuantity -= item.Quantity
            inv.AllocatedQuantity += item.Quantity
            inv.UpdatedAt = now
            inventory_ledger.record(db, inv, InventoryMovementType.Distributed, item.Quantity, actor.user_id, token.TokenNumber)
        token.Status = int(TokenStatus.Completed)
        token.CollectedAt = now
        # A unique placeholder, replaced by COL-DEMO-{id} once the id exists (the code column is unique).
        collection = RationCollection(CollectionCode=f"PENDING-{uuid.uuid4().hex}", TokenId=token.Id, BeneficiaryId=beneficiary_id,
                                      RationShopId=token.RationShopId, OperatorUserId=actor.user_id, VerificationMethod=method,
                                      IdempotencyKey=idempotency_key or None, CollectedAt=now)
        db.add(collection)
        db.flush()
        collection.CollectionCode = f"COL-DEMO-{collection.Id:06d}"
        db.add_all(RationCollectionItem(RationCollectionId=collection.Id, RationType=i.RationType, Quantity=i.Quantity) for i in requested)
        audit_service.record(db, actor.user_id, "COLLECTION_COMPLETED", "Token", str(token.Id),
                             f"{token.TokenNumber} {collection.CollectionCode} via {method}", role=actor.role.name, ip_address=actor.ip_address)
        verification_audit_service.log(db, actor, VerificationAction.CollectionConfirmed, "SUCCESS", method,
                                       token_number=token.TokenNumber, beneficiary_id=beneficiary_id, shop_id=token.RationShopId)
        db.commit()
    except IntegrityError:
        # Unique TokenId / IdempotencyKey: someone else completed this at the same moment. Nothing was saved.
        db.rollback()
        log.warning("Collection for token %s lost a concurrent update; rolled back.", token_id)
        raise Conflict("Could not complete the collection due to a concurrent update. Please try again.", "CONCURRENT_UPDATE") from None
    except Exception:
        db.rollback()
        raise

    log.info("Collection confirmed: %s for token %s via %s", collection.CollectionCode, token.TokenNumber, method)
    notification_service.create(db, token.UserId, NotificationType.CollectionCompleted, "Ration collected",
                                f"Your ration for token {token.TokenNumber} has been collected. Collection ID {collection.CollectionCode}.")
    db.commit()
    return _receipt(collection.CollectionCode, token.TokenNumber, verification["beneficiary"]["fullName"],
                    verification["family"]["familySize"], verification["entitlement"]["schemeCode"],
                    [(i.RationType, i.Quantity) for i in requested], verification["booking"]["shopName"], collection.CollectedAt)
