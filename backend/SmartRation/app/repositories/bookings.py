"""Booking tokens (Tokens + TimeSlots). Every query takes the user id explicitly: callers pass the id
from a verified access token, never one taken from a request body or chat message."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.database.models import RationShop, TimeSlot, Token


def upcoming_for_user(db: Session, user_id: int, since: datetime, statuses: Collection[int], limit: int) -> Sequence[Row]:
    """The user's bookings in `statuses` whose slot date is on/after `since`, soonest first.
    Rows: Id, TokenNumber, Status, SlotDate, StartTime, EndTime, ShopName."""
    return db.execute(
        select(Token.Id, Token.TokenNumber, Token.Status, TimeSlot.SlotDate, TimeSlot.StartTime, TimeSlot.EndTime, RationShop.ShopName)
        .join(TimeSlot, TimeSlot.Id == Token.TimeSlotId)
        .join(RationShop, RationShop.Id == Token.RationShopId)
        .where(Token.UserId == user_id, Token.Status.in_(statuses), TimeSlot.SlotDate >= since)
        .order_by(TimeSlot.SlotDate, TimeSlot.StartTime)
        .limit(limit)
    ).all()
