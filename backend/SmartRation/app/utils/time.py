"""Timestamps in the form the shared MySQL database and the C# API use."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Naive UTC, the way EF Core stores DateTime in this database."""
    return datetime.now(UTC).replace(tzinfo=None)


def format_utc(value: datetime) -> str:
    """ISO-8601 with 7 fractional digits and 'Z', matching .NET's DateTime(Kind=Utc) JSON."""
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f") + "0Z"
