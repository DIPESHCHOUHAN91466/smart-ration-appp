"""Timestamps in the form the shared MySQL database and the C# API use, and the shops' business clock.

Business-time policy (2026-10-17):
  * Timestamps (CreatedAt, CollectedAt, ExpiresAt, ...) are stored and compared in naive UTC.
  * Calendar dates and opening hours (TimeSlot.SlotDate / StartTime) are Asia/Kolkata wall-clock values.
  * "Today", "this month", "has this slot started", "has the booked day ended" are answered on the Asia/Kolkata clock;
    when such a day or month is compared with a timestamp, its bounds are converted to UTC first.
The zone comes from the IANA database (`zoneinfo`); the pinned `tzdata` package in requirements.txt provides it where the
operating system has none (slim images), so a missing database fails at import instead of silently using UTC.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

BUSINESS_TIMEZONE = ZoneInfo("Asia/Kolkata")


def utc_now() -> datetime:
    """Naive UTC, the way EF Core stores DateTime in this database."""
    return datetime.now(UTC).replace(tzinfo=None)


def business_now(now_utc: datetime | None = None) -> datetime:
    """Naive wall-clock time in Asia/Kolkata. Slot dates and opening hours (TimeSlot.SlotDate/StartTime) are kept in
    this clock, timestamps in UTC. `now_utc` (naive UTC) is for tests; by default the current time."""
    utc = utc_now() if now_utc is None else now_utc
    return utc.replace(tzinfo=UTC).astimezone(BUSINESS_TIMEZONE).replace(tzinfo=None)


def business_today(now_utc: datetime | None = None) -> datetime:
    """Midnight of the current Asia/Kolkata date (the form TimeSlot.SlotDate is stored in)."""
    return business_now(now_utc).replace(hour=0, minute=0, second=0, microsecond=0)


def business_to_utc(local: datetime) -> datetime:
    """An Asia/Kolkata wall-clock time (naive) as naive UTC, for comparing with stored timestamps."""
    return local.replace(tzinfo=BUSINESS_TIMEZONE).astimezone(UTC).replace(tzinfo=None)


def business_day_utc(day: datetime) -> tuple[datetime, datetime]:
    """[start, end) of the Asia/Kolkata calendar day `day` (any time on it), as naive UTC."""
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    return business_to_utc(start), business_to_utc(start + timedelta(days=1))


def business_month_utc(now_utc: datetime | None = None) -> tuple[datetime, datetime]:
    """[start, end) of the current Asia/Kolkata calendar month, as naive UTC (the monthly entitlement window)."""
    start = business_today(now_utc).replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1)
    return business_to_utc(start), business_to_utc(end)


def slot_has_started(slot_date: datetime, start: time, now_utc: datetime | None = None) -> bool:
    """True once the slot's start (its date + start time, Asia/Kolkata) is now or past. A slot starting exactly now has
    started, the same rule as the Android app (Slot.hasStarted): a citizen can't be at the counter already."""
    return datetime.combine(slot_date.date(), start) <= business_now(now_utc)


def format_utc(value: datetime) -> str:
    """ISO-8601 with 7 fractional digits and 'Z', matching .NET's DateTime(Kind=Utc) JSON."""
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f") + "0Z"
