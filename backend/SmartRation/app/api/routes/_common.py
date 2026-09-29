"""Small helpers shared by the migrated route modules."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Literal, overload

from fastapi import Request

from app.core.body import Body, request_json
from app.core.validation import ValidationFailed


async def json_body(request: Request) -> Body:
    """Dependency: the request's JSON body as a Body (400 if it is not a JSON object)."""
    return Body(await request_json(request))


def settings_of(request: Request) -> Any:
    return request.app.state.settings


@overload
def parse_date(field: str, raw: str | None, *, required: Literal[True] = True) -> datetime: ...
@overload
def parse_date(field: str, raw: str | None, *, required: bool) -> datetime | None: ...


def parse_date(field: str, raw: str | None, *, required: bool = True) -> datetime | None:
    """'2026-09-29' or an ISO date-time -> midnight of that day. Submitted values are never echoed back."""
    if raw is None or raw == "":
        if required:
            raise ValidationFailed([f"{field}: The {field} field is required."])
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00")) if "T" in raw else datetime.combine(date.fromisoformat(raw), time())
    except ValueError:
        raise ValidationFailed([f"{field}: The value is not a valid date."]) from None
    return value.replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)


def parse_timespan(field: str, raw: Any, errors: list[str]) -> time:
    """.NET TimeSpan text 'HH:MM' or 'HH:MM:SS' -> time. Problems are appended to `errors` (and midnight
    returned as a placeholder that is never used, because the caller raises on errors first)."""
    if raw is None or raw == "":
        errors.append(f"{field}: The {field} field is required.")
        return time()
    if not isinstance(raw, str):
        errors.append(f"$.{field[0].lower()}{field[1:]}: The JSON value could not be converted to System.TimeSpan.")
        return time()
    try:
        parts = [int(p) for p in raw.split(":")]
        if len(parts) not in (2, 3):
            raise ValueError
        return time(parts[0], parts[1], parts[2] if len(parts) == 3 else 0)
    except ValueError:
        errors.append(f"$.{field[0].lower()}{field[1:]}: The JSON value could not be converted to System.TimeSpan.")
        return time()


def idempotency_key(request: Request) -> str | None:
    value = request.headers.get("Idempotency-Key")
    return value or None
