"""AuditLogs writer — same table and fields as the C# AuditLogService.

Adds the row to the caller's session; the caller commits (so an audit row is
atomic with the change it describes). Never pass passwords, tokens, full
Aadhaar numbers or other personal data in `details` (mask with app.utils.masking).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories import audit_logs
from app.utils.time import utc_now


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
    audit_logs.add(db, user_id=user_id, action=action, entity_name=entity_name, entity_id=entity_id, details=details,
                   result=result, role=role, ip_address=ip_address, created_at=utc_now())
