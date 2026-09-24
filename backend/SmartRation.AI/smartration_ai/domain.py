"""Enum values and value parsing shared with the .NET model.

Integer values mirror backend/SmartRation.Api/Models — keep them in sync.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal

RATION_TYPES = {1: "Rice", 2: "Wheat", 3: "Sugar", 4: "Pulses", 5: "EdibleOil", 6: "Salt"}
RATION_UNITS = {"EdibleOil": "L"}  # everything else is kg


class TokenStatus:
    PENDING = 1
    CONFIRMED = 2
    COMPLETED = 3
    CANCELLED = 4
    NO_SHOW = 5


class VerificationAction:
    QR_SCANNED = 1
    BENEFICIARY_VERIFIED = 2
    OTP_FAILED = 7
    COLLECTION_REJECTED = 9
    TOKEN_ALREADY_USED = 10


class MovementType:
    RECEIVED = 1
    DISTRIBUTED = 2
    DAMAGED = 3
    ADJUSTMENT = 4


ELIGIBLE = 1  # EligibilityStatus.Eligible


def unit_for(ration_type: str) -> str:
    return RATION_UNITS.get(ration_type, "kg")


def as_float(value) -> float:
    """SQLite stores EF decimals as TEXT, MySQL returns Decimal."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    return float(Decimal(str(value)))


def as_datetime(value) -> datetime | None:
    """Parse EF datetimes: MySQL gives datetime; SQLite gives text with up to 7 fraction digits."""
    if value is None or isinstance(value, datetime):
        return value
    text = str(value).replace("T", " ").rstrip("Z")
    if "." in text:
        head, frac = text.split(".", 1)
        text = f"{head}.{frac[:6]}"
    return datetime.fromisoformat(text)


def as_date(value) -> date | None:
    parsed = as_datetime(value)
    return parsed.date() if parsed else None


def as_time(value) -> time:
    """TimeSpan columns: MySQL returns timedelta (TIME), SQLite returns 'HH:MM:SS'."""
    if isinstance(value, timedelta):
        return (datetime.min + value).time()
    if isinstance(value, time):
        return value
    return time.fromisoformat(str(value)[:8])
