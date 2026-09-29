"""Value formatting that keeps the API's JSON exactly as the frontend has always received it.

The business API was first written in ASP.NET Core; its responses (and so the React app) use these
formats. Python produces the same text so nothing in the browser has to change:

    DateTime       "2026-09-24T02:48:52.118892"  (no zone; UTC by convention; trailing zeros trimmed)
    TimeSpan       "09:10:00"
    date strings   "2026-09-24", "2026-09-24 09:10", "September 2026"
    decimal        a JSON number (never a string)
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal


def dt(value: datetime | date | None) -> str | None:
    """ISO-8601 like System.Text.Json writes an unspecified-kind DateTime."""
    if value is None:
        return None
    if not isinstance(value, datetime):
        value = datetime(value.year, value.month, value.day)
    text = value.strftime("%Y-%m-%dT%H:%M:%S")
    if value.microsecond:
        text += "." + f"{value.microsecond:06d}".rstrip("0")
    return text


def timespan(value: time | timedelta | None) -> str | None:
    """'hh:mm:ss' like a .NET TimeSpan (slot start/end times)."""
    if value is None:
        return None
    if isinstance(value, timedelta):
        total = int(value.total_seconds())
        return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"
    return value.strftime("%H:%M:%S")


def hhmm(value: time | None) -> str:
    return value.strftime("%H:%M") if value else ""


def ymd(value: datetime | date | None) -> str | None:
    return value.strftime("%Y-%m-%d") if value else None


def ymd_hm(value: datetime | None) -> str | None:
    return value.strftime("%Y-%m-%d %H:%M") if value else None


def ymd_hms(value: datetime | None) -> str | None:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


def month_year(value: datetime | None) -> str | None:
    return value.strftime("%B %Y") if value else None


def num(value: Decimal | float | int | None) -> float | int | None:
    """A decimal as a JSON number; whole numbers stay integers."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def qty_text(value: Decimal | float | int) -> str:
    """A quantity inside a sentence: '85', '0.75' (no trailing zeros)."""
    d = Decimal(str(value)).normalize()
    return format(d, "f")


def one_decimal(value: float) -> str:
    """.NET '0.#' format: at most one decimal, no trailing zero."""
    rounded = round(value, 1)
    return str(int(rounded)) if rounded == int(rounded) else f"{rounded:.1f}"


def midnight(value: datetime) -> datetime:
    return value.replace(hour=0, minute=0, second=0, microsecond=0)
