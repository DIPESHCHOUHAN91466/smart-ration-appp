"""Bookings (= ration tokens): create, list, view, reschedule, cancel, and a shop's queue for today.

Rules:
  * one active booking per citizen per slot; never a slot in the past; never more bookings than the
    slot's capacity — the slot row is locked while it is checked and counted (SELECT ... FOR UPDATE), so
    two citizens can't take the last place at the same moment;
  * every item must be an active catalog item, within its per-visit quota and in stock at the shop;
  * token number SR-{year}-{id:06}; its QR reference is signed with QR_SECRET;
  * access: citizens their own bookings, shop owners their shop's, officials all.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound
from app.database.enums import NotificationType, RationType, TokenStatus, UserRole, parse_enum
from app.database.models import Inventory, RationItem, RationShop, TimeSlot, Token, TokenItem
from app.services import audit_service, notification_service
from app.services.mappers import token_dto, token_dtos
from app.services.qr_service import compute_reference
from app.utils.dotnet import hhmm, midnight, qty_text
from app.utils.time import utc_now

ACTIVE = (int(TokenStatus.Pending), int(TokenStatus.Confirmed))


def _can_access(actor: Actor, token: Token) -> bool:
    if actor.role == UserRole.RuralUser:
        return token.UserId == actor.user_id
    if actor.role == UserRole.ShopOwner:
        return token.RationShopId == actor.ration_shop_id
    return actor.role in (UserRole.GovernmentOfficial, UserRole.Admin)


def _load(db: Session, actor: Actor, token_id: int, *, lock: bool = False) -> Token:
    q = select(Token).where(Token.Id == token_id)
    token = db.scalar(q.with_for_update() if lock else q)
    if token is None:
        raise NotFound("Booking not found.")
    if not _can_access(actor, token):
        raise Forbidden("You do not have access to this booking.")
    return token


def _resolve_items(db: Session, shop_id: int, items: list[tuple[str, Decimal]]) -> list[tuple[RationType, Decimal]]:
    resolved = []
    for name, qty in items:
        rtype = parse_enum(RationType, name)
        if rtype is None:
            raise BadRequest(f"Unknown ration item '{name}'.")
        catalog = db.scalar(select(RationItem).where(RationItem.RationType == int(rtype), RationItem.IsActive.is_(True)))
        if catalog is None:
            raise BadRequest(f"'{name}' is not currently available.")
        if qty <= 0 or qty > catalog.StandardQuotaPerBooking:
            raise BadRequest(f"Quantity for {catalog.Name} must be between 0 and the standard quota of "
                             f"{qty_text(catalog.StandardQuotaPerBooking)} {catalog.Unit}.")
        stock = db.scalar(select(Inventory).where(Inventory.RationShopId == shop_id, Inventory.RationType == int(rtype)))
        if stock is None or stock.AvailableQuantity < qty:
            raise BadRequest(f"Insufficient {catalog.Name} stock at this shop.")
        resolved.append((rtype, qty))
    return resolved


def create(db: Session, secret: str, actor: Actor, shop_id: int, slot_id: int, items: list[tuple[str, Decimal]]) -> dict:
    shop = db.scalar(select(RationShop).where(RationShop.Id == shop_id, RationShop.IsActive.is_(True)))
    if shop is None:
        raise NotFound("Ration shop not found or inactive.")
    slot = db.scalar(select(TimeSlot).where(TimeSlot.Id == slot_id, TimeSlot.RationShopId == shop_id).with_for_update())
    if slot is None:
        raise NotFound("Time slot not found for this shop.")
    if midnight(slot.SlotDate) < midnight(utc_now()):
        raise BadRequest("Cannot book a time slot in the past.")
    duplicate = db.scalar(select(Token.Id).where(Token.UserId == actor.user_id, Token.TimeSlotId == slot.Id, Token.Status.in_(ACTIVE)))
    if duplicate:
        raise Conflict("You already have an active booking for this time slot.")
    resolved = _resolve_items(db, shop.Id, items)
    if slot.BookedCount >= slot.Capacity:
        raise Conflict("This time slot is full. Please choose another slot.")

    slot.BookedCount += 1
    now = utc_now()
    token = Token(TokenNumber="", UserId=actor.user_id, RationShopId=shop.Id, TimeSlotId=slot.Id,
                  Status=int(TokenStatus.Confirmed), CreatedAt=now)
    db.add(token)
    db.flush()
    token.TokenNumber = f"SR-{now:%Y}-{token.Id:06d}"
    token.QRCodeValue = compute_reference(secret, token.Id, token.TokenNumber)
    db.add_all(TokenItem(TokenId=token.Id, RationType=int(t), Quantity=q) for t, q in resolved)
    audit_service.record(db, actor.user_id, "BOOKING_CREATED", "Token", str(token.Id), token.TokenNumber,
                         role=actor.role.name, ip_address=actor.ip_address)
    notification_service.create(db, actor.user_id, NotificationType.TokenGenerated, "Ration token generated",
                                f"Your token {token.TokenNumber} is confirmed for {slot.SlotDate:%Y-%m-%d} at {hhmm(slot.StartTime)}.")
    db.commit()
    return token_dto(db, token)


def list_for(db: Session, actor: Actor) -> list[dict]:
    q = select(Token)
    if actor.role == UserRole.RuralUser:
        q = q.where(Token.UserId == actor.user_id)
    elif actor.role == UserRole.ShopOwner:
        q = q.where(Token.RationShopId == actor.ration_shop_id)
    return token_dtos(db, db.scalars(q.order_by(Token.CreatedAt.desc(), Token.Id.desc())).all())


def get(db: Session, actor: Actor, token_id: int) -> dict:
    return token_dto(db, _load(db, actor, token_id))


def reschedule(db: Session, actor: Actor, token_id: int, new_slot_id: int) -> dict:
    token = _load(db, actor, token_id, lock=True)
    if token.Status != TokenStatus.Confirmed:
        raise BadRequest(f"Cannot reschedule a booking in {TokenStatus(token.Status).name} status.")
    new_slot = db.scalar(select(TimeSlot).where(TimeSlot.Id == new_slot_id, TimeSlot.RationShopId == token.RationShopId).with_for_update())
    if new_slot is None:
        raise NotFound("Time slot not found for this shop.")
    if new_slot.Id == token.TimeSlotId:
        return token_dto(db, token)
    if midnight(new_slot.SlotDate) < midnight(utc_now()):
        raise BadRequest("Cannot reschedule to a time slot in the past.")
    if new_slot.BookedCount >= new_slot.Capacity:
        raise Conflict("The selected time slot is full.")
    old_slot = db.scalar(select(TimeSlot).where(TimeSlot.Id == token.TimeSlotId).with_for_update())
    if old_slot is not None:
        old_slot.BookedCount = max(0, old_slot.BookedCount - 1)
    new_slot.BookedCount += 1
    token.TimeSlotId = new_slot.Id
    audit_service.record(db, actor.user_id, "BOOKING_RESCHEDULED", "Token", str(token.Id), role=actor.role.name, ip_address=actor.ip_address)
    db.commit()
    return token_dto(db, token)


def cancel(db: Session, actor: Actor, token_id: int) -> None:
    token = _load(db, actor, token_id, lock=True)
    if token.Status in (TokenStatus.Completed, TokenStatus.Cancelled):
        raise BadRequest(f"Cannot cancel a booking that is already {TokenStatus(token.Status).name}.")
    token.Status = int(TokenStatus.Cancelled)
    slot = db.scalar(select(TimeSlot).where(TimeSlot.Id == token.TimeSlotId).with_for_update())
    if slot is not None:
        slot.BookedCount = max(0, slot.BookedCount - 1)   # a cancelled booking gives its place back
    audit_service.record(db, actor.user_id, "BOOKING_CANCELLED", "Token", str(token.Id), role=actor.role.name, ip_address=actor.ip_address)
    notification_service.create(db, token.UserId, NotificationType.BookingCancelled, "Booking cancelled",
                                f"Your ration token {token.TokenNumber} has been cancelled.")
    db.commit()


def today_queue(db: Session, actor: Actor) -> list[dict]:
    if actor.ration_shop_id is None:
        raise BadRequest("Your account is not linked to a ration shop.")
    today = midnight(utc_now())
    rows = db.execute(
        select(Token, TimeSlot.StartTime).join(TimeSlot, TimeSlot.Id == Token.TimeSlotId)
        .where(Token.RationShopId == actor.ration_shop_id, TimeSlot.SlotDate >= today, TimeSlot.SlotDate < today + timedelta(days=1))
        .order_by(TimeSlot.StartTime, Token.Id)
    ).all()
    return token_dtos(db, [t for t, _ in rows])
