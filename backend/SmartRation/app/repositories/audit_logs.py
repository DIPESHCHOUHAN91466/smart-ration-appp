"""AuditLogs table: append-only. There is deliberately no update or delete here."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import AuditLog


def add(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_name: str,
    entity_id: str | None,
    details: str | None,
    result: str,
    role: str | None,
    ip_address: str | None,
    created_at: datetime,
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
        CreatedAt=created_at,
    ))
