"""AuditLogs writer — same table and fields as the C# AuditLogService.

Adds the row to the caller's session; the caller commits (so an audit row is
atomic with the change it describes). Never pass passwords, tokens, full
Aadhaar numbers or other personal data in `details`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import utc_now
from app.db.models import AuditLog


def record(
    db: Session,
    user_id: int | None,
    action: str,
    entity_name: str,
    entity_id: str | None = None,
    details: str | None = None,
    result: str = "SUCCESS",
    role: str | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(AuditLog(
        UserId=user_id,
        Action=action,
        EntityName=entity_name,
        EntityId=entity_id,
        IpAddress=ip_address,
        Details=details,
        Role=role,
        Result=result,
        CreatedAt=utc_now(),
    ))


def mask_email(email: str) -> str:
    """'rahul@example.com' -> 'r***@example.com' (same as the C# MaskEmail)."""
    at = email.find("@")
    return "***" if at <= 0 else f"{email[0]}***{email[at:]}"
