"""5-minute collection time slots: list a shop's slots for a day, create, change capacity, and keep the
next days' slots available in synthetic (demo) mode.

Shop owners manage only their own shop's slots; officials any shop's.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound
from app.database.enums import UserRole
from app.database.models import RationShop, TimeSlot
from app.services.mappers import slot_dto
from app.utils.dotnet import midnight
from app.utils.time import utc_now

# The shops' opening hours used when slots are generated (09:00-17:00, 5 minutes each).
OPEN, CLOSE, MINUTES, DEFAULT_CAPACITY = 9 * 60, 17 * 60, 5, 2


def _ensure_can_manage(actor: Actor, shop_id: int) -> None:
    allowed = (actor.role == UserRole.ShopOwner and actor.ration_shop_id == shop_id) or actor.role in (UserRole.GovernmentOfficial, UserRole.Admin)
    if not allowed:
        raise Forbidden("You do not have permission to manage time slots for this shop.")


def list_for_day(db: Session, shop_id: int, day: datetime) -> list[dict]:
    if db.get(RationShop, shop_id) is None:
        raise NotFound("Ration shop not found.")
    start = midnight(day)
    slots = db.scalars(select(TimeSlot).where(TimeSlot.RationShopId == shop_id, TimeSlot.SlotDate >= start,
                                              TimeSlot.SlotDate < start + timedelta(days=1))
                       .order_by(TimeSlot.StartTime, TimeSlot.Id)).all()
    return [slot_dto(s) for s in slots]


def create(db: Session, actor: Actor, shop_id: int, day: datetime, start: time, end: time, capacity: int) -> dict:
    if db.get(RationShop, shop_id) is None:
        raise NotFound("Ration shop not found.")
    _ensure_can_manage(actor, shop_id)
    if end <= start:
        raise BadRequest("End time must be after start time.")
    day = midnight(day)
    overlap = db.scalar(select(TimeSlot.Id).where(TimeSlot.RationShopId == shop_id, TimeSlot.SlotDate >= day,
                                                  TimeSlot.SlotDate < day + timedelta(days=1),
                                                  TimeSlot.StartTime < end, TimeSlot.EndTime > start))
    if overlap:
        raise Conflict("This time slot overlaps with an existing slot for this shop.")
    slot = TimeSlot(RationShopId=shop_id, SlotDate=day, StartTime=start, EndTime=end, Capacity=capacity, BookedCount=0)
    db.add(slot)
    db.commit()
    return slot_dto(slot)


def update_capacity(db: Session, actor: Actor, slot_id: int, capacity: int) -> dict:
    slot = db.scalar(select(TimeSlot).where(TimeSlot.Id == slot_id).with_for_update())
    if slot is None:
        raise NotFound("Time slot not found.")
    _ensure_can_manage(actor, slot.RationShopId)
    if capacity < slot.BookedCount:
        raise BadRequest(f"Capacity cannot be less than the {slot.BookedCount} beneficiaries already booked into this slot.")
    slot.Capacity = capacity
    db.commit()
    return slot_dto(slot)


def ensure_upcoming(db: Session, days: int, capacity: int = DEFAULT_CAPACITY) -> int:
    """Synthetic (demo) mode: make sure every active shop has 5-minute slots from today for `days` days.
    Only days with no slots at all are filled, so shop-edited days are never touched. Returns slots added."""
    today = midnight(utc_now())
    added = 0
    for shop_id in db.scalars(select(RationShop.Id).where(RationShop.IsActive.is_(True))).all():
        for offset in range(days):
            day = today + timedelta(days=offset)
            exists = db.scalar(select(func.count()).select_from(TimeSlot).where(
                TimeSlot.RationShopId == shop_id, TimeSlot.SlotDate >= day, TimeSlot.SlotDate < day + timedelta(days=1)))
            if exists:
                continue
            for minute in range(OPEN, CLOSE, MINUTES):
                db.add(TimeSlot(RationShopId=shop_id, SlotDate=day, StartTime=time(minute // 60, minute % 60),
                                EndTime=time((minute + MINUTES) // 60, (minute + MINUTES) % 60), Capacity=capacity, BookedCount=0))
                added += 1
    db.commit()
    return added
