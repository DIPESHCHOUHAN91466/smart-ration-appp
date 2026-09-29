"""The verification audit trail: every QR scan, identity check, OTP step and collection decision.

Deliberately never stores Aadhaar numbers, mobile numbers, OTP codes or raw QR payloads — only the
operational facts (who, where, which token, outcome, reason). Rows are added to the caller's session
and saved with the surrounding change.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.database.enums import VerificationAction
from app.database.models import VerificationAuditLog
from app.utils.dotnet import ymd_hms
from app.utils.time import utc_now


def log(db: Session, actor: Actor | None, action: VerificationAction, status: str, method: str, *,
        reference: str | None = None, token_number: str | None = None, beneficiary_id: int | None = None,
        shop_id: int | None = None, reason: str | None = None) -> None:
    db.add(VerificationAuditLog(
        VerificationReference=reference, TokenNumber=token_number, BeneficiaryId=beneficiary_id, ShopId=shop_id,
        Action=int(action), VerificationMethod=method, Status=status, Reason=reason,
        OperatorId=actor.user_id if actor else None,
        DeviceInfo=(actor.user_agent or "")[:512] if actor else None,
        IpAddress=actor.ip_address if actor else None,
        Timestamp=utc_now(),
    ))


def to_dto(row: VerificationAuditLog) -> dict:
    return {
        "id": row.Id, "verificationReference": row.VerificationReference, "tokenNumber": row.TokenNumber,
        "beneficiaryId": row.BeneficiaryId, "shopId": row.ShopId, "action": VerificationAction(row.Action).name,
        "verificationMethod": row.VerificationMethod, "status": row.Status, "reason": row.Reason,
        "operatorId": row.OperatorId, "timestamp": ymd_hms(row.Timestamp),
    }


def query(db: Session, shop_id: int | None, beneficiary_id: int | None, status: str | None, take: int) -> list[dict]:
    q = select(VerificationAuditLog)
    if shop_id is not None:
        q = q.where(VerificationAuditLog.ShopId == shop_id)
    if beneficiary_id is not None:
        q = q.where(VerificationAuditLog.BeneficiaryId == beneficiary_id)
    if status and status.strip():
        q = q.where(VerificationAuditLog.Status == status)
    rows = db.scalars(q.order_by(VerificationAuditLog.Timestamp.desc(), VerificationAuditLog.Id.desc())
                      .limit(max(1, min(take, 500)))).all()
    return [to_dto(r) for r in rows]
