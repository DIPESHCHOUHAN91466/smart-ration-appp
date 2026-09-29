"""The shop counter: today's dashboard, the global QR scanner and the "mark collected" queue button.

Both the scanner and the queue button end in collection_service.confirm, so there is exactly one,
authoritative path that issues ration.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import ApiError, BadRequest, Forbidden, NotFound
from app.database.enums import TokenStatus, UserRole
from app.database.models import Inventory, RationShop, TimeSlot, Token
from app.services import collection_service, verification_service
from app.services.mappers import inventory_dto, token_dto
from app.services.qr_service import QrScanStatus
from app.services.verification_service import READY
from app.utils.dotnet import midnight
from app.utils.time import utc_now


def _require_shop(actor: Actor) -> int:
    if actor.role != UserRole.ShopOwner:
        raise Forbidden("Only shop owners can access this resource.")
    if actor.ration_shop_id is None:
        raise BadRequest("Your account is not linked to a ration shop.")
    return actor.ration_shop_id


def dashboard(db: Session, actor: Actor) -> dict:
    shop_id = _require_shop(actor)
    shop = db.get(RationShop, shop_id)
    if shop is None:
        raise NotFound("Ration shop not found.")
    today = midnight(utc_now())
    statuses = db.scalars(select(Token.Status).join(TimeSlot, TimeSlot.Id == Token.TimeSlotId)
                          .where(Token.RationShopId == shop_id, TimeSlot.SlotDate >= today,
                                 TimeSlot.SlotDate < today + timedelta(days=1))).all()
    inventory = db.scalars(select(Inventory).where(Inventory.RationShopId == shop_id).order_by(Inventory.RationType)).all()
    return {"shopId": shop.Id, "shopName": shop.ShopName, "todayTotalTokens": len(statuses),
            "todayCompleted": sum(1 for s in statuses if s == TokenStatus.Completed),
            "todayPending": sum(1 for s in statuses if s in (TokenStatus.Pending, TokenStatus.Confirmed)),
            "todayCancelled": sum(1 for s in statuses if s == TokenStatus.Cancelled),
            "inventory": [inventory_dto(i) for i in inventory]}


def complete_collection(db: Session, actor: Actor, token_id: int, idempotency_key: str | None) -> dict:
    shop_id = _require_shop(actor)
    token = db.get(Token, token_id)
    if token is None:
        raise NotFound("Token not found.")
    if token.RationShopId != shop_id:
        raise Forbidden("This token belongs to a different ration shop.")
    collection_service.confirm(db, actor, token.Id, "QUEUE", idempotency_key)
    db.refresh(token)
    return token_dto(db, token)


def scan(db: Session, secret: str, actor: Actor, qr_data: str | None) -> dict:
    """Every validation outcome comes back as a structured status (HTTP 200), not an HTTP error, so the
    scanner can show a specific, translated result screen."""
    try:
        v = verification_service.verify_by_qr(db, secret, actor, qr_data or "")
    except ApiError as exc:
        if exc.error_code is None:
            raise
        return {"verified": False, "status": exc.error_code, "message": exc.message, "tokenNumber": None, "verification": None}

    summary, booking = v["verificationSummary"], v["booking"]
    ready = summary["overallStatus"] == READY
    if ready:
        status = QrScanStatus.VERIFIED
    elif booking["status"] == TokenStatus.Completed.name:
        status = QrScanStatus.ALREADY_COLLECTED
    elif booking["status"] == TokenStatus.Cancelled.name:
        status = QrScanStatus.BOOKING_CANCELLED
    elif datetime.strptime(booking["collectionDate"], "%Y-%m-%d") < midnight(utc_now()):
        status = QrScanStatus.EXPIRED
    else:
        status = QrScanStatus.NOT_ELIGIBLE
    return {"verified": ready, "status": status,
            "message": "QR verified successfully" if ready else (summary["blockedReason"] or "Collection is blocked."),
            "tokenNumber": booking["tokenNumber"], "verification": v}
