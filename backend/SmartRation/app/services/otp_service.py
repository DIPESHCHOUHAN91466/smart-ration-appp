"""One-time passwords: the fallback when a QR code can't be scanned.

Only a SHA-256 hash of each code is stored. Only the newest code for a beneficiary is valid; a new one
can be requested after a cooldown; a code expires after OTP_EXPIRY_MINUTES and after OTP_MAX_ATTEMPTS
wrong tries. DEMO mode (DEMO_OTP_ENABLED, refused outside development) issues a fixed code instead of a
random one. The SMS text contains the code, so it is never logged — only the masked number.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.core.errors import BadRequest, Forbidden, NotFound, ServiceUnavailable
from app.database.enums import OtpStatus
from app.database.models import Beneficiary, OtpVerification, User
from app.services._db import require
from app.utils.masking import mask_mobile
from app.utils.time import utc_now

log = logging.getLogger("smartration.otp")


@dataclass(frozen=True)
class SmsResult:
    sent: bool
    provider: str
    error: str | None = None


def send_sms(settings: Settings, phone: str, message: str) -> SmsResult:
    """'mock': sends nothing (development / synthetic demo). 'http': JSON POST to a DLT-registered gateway."""
    if settings.sms_provider.lower() != "http":
        log.info("[MOCK SMS] Not sent", extra={"fields": {"to": mask_mobile(phone), "chars": len(message), "id": f"mock-{uuid.uuid4().hex}"}})
        return SmsResult(True, "Mock")
    if not settings.sms_base_url or not settings.sms_api_key:
        return SmsResult(False, "Http", "SMS gateway is not configured.")
    try:
        response = httpx.post(settings.sms_base_url, json={"to": phone, "sender": settings.sms_sender_id, "message": message},
                              headers={"Authorization": f"Bearer {settings.sms_api_key}"}, timeout=10)
    except httpx.HTTPError as exc:
        log.warning("SMS gateway unreachable", extra={"fields": {"to": mask_mobile(phone), "error": type(exc).__name__}})
        return SmsResult(False, "Http", "SMS gateway unreachable.")
    if response.status_code >= 400:
        log.warning("SMS gateway error", extra={"fields": {"to": mask_mobile(phone), "status": response.status_code}})
        return SmsResult(False, "Http", f"Gateway returned {response.status_code}.")
    return SmsResult(True, "Http")


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest().upper()


def request_for_mobile(db: Session, settings: Settings, mobile: str, requested_by: int) -> OtpVerification:
    beneficiary_id = db.scalar(select(Beneficiary.Id).join(User, User.Id == Beneficiary.UserId)
                               .where(User.MobileNumber == mobile).limit(1))
    if beneficiary_id is None:
        raise NotFound("No beneficiary is registered with this mobile number.")
    return request(db, settings, beneficiary_id, requested_by)


def request(db: Session, settings: Settings, beneficiary_id: int, requested_by: int) -> OtpVerification:
    beneficiary = db.get(Beneficiary, beneficiary_id)
    if beneficiary is None:
        raise NotFound("Beneficiary not found.")
    if not beneficiary.IsActive or beneficiary.IsBlocked:
        raise Forbidden("This beneficiary account is not active.")
    now = utc_now()
    pending = db.scalars(select(OtpVerification).where(OtpVerification.BeneficiaryId == beneficiary_id,
                                                       OtpVerification.Status == int(OtpStatus.Pending))).all()
    newest = max(pending, key=lambda o: o.CreatedAt, default=None)
    if newest is not None:
        wait = settings.otp_resend_cooldown_seconds - int((now - newest.CreatedAt).total_seconds())
        if wait > 0:
            raise BadRequest(f"Please wait {wait} seconds before requesting another OTP.", "OTP_COOLDOWN")
    for old in pending:
        old.Status = int(OtpStatus.Expired)    # only the newest code is ever valid

    code = settings.demo_otp_value if settings.demo_otp_enabled else f"{secrets.randbelow(1_000_000):06d}"
    record = OtpVerification(BeneficiaryId=beneficiary_id, RequestedByUserId=requested_by, OtpHash=_hash(code), AttemptCount=0,
                             MaxAttempts=settings.otp_max_attempts, Status=int(OtpStatus.Pending), CreatedAt=now,
                             ExpiresAt=now + timedelta(minutes=settings.otp_expiry_minutes))
    db.add(record)
    db.commit()
    user = require(db, User, beneficiary.UserId, "User not found.")
    sent = send_sms(settings, user.MobileNumber,
                    f"Your Smart Ration verification code is {code}. Valid for {settings.otp_expiry_minutes} minutes. Do not share it.")
    if not sent.sent:
        record.Status = int(OtpStatus.Failed)   # an undeliverable code must not stay usable
        db.commit()
        raise ServiceUnavailable("Could not send the OTP right now. Please try again or use QR verification.", "SMS_UNAVAILABLE")
    return record


def verify(db: Session, otp_id: int, code: str) -> OtpVerification:
    record = db.scalar(select(OtpVerification).where(OtpVerification.Id == otp_id).with_for_update())
    if record is None:
        raise NotFound("OTP request not found.")
    if record.Status != OtpStatus.Pending:
        raise BadRequest(f"This OTP request is already {OtpStatus(record.Status).name}.")
    if utc_now() > record.ExpiresAt:
        record.Status = int(OtpStatus.Expired)
        db.commit()
        raise BadRequest("OTP has expired. Please request a new one.")
    if record.AttemptCount >= record.MaxAttempts:
        record.Status = int(OtpStatus.Failed)
        db.commit()
        raise BadRequest("Maximum OTP attempts exceeded. Please request a new one.")
    if not secrets.compare_digest(_hash(code), record.OtpHash):
        record.AttemptCount += 1
        if record.AttemptCount >= record.MaxAttempts:
            record.Status = int(OtpStatus.Failed)
        db.commit()
        raise BadRequest(f"Incorrect OTP. {max(0, record.MaxAttempts - record.AttemptCount)} attempt(s) remaining.")
    record.Status = int(OtpStatus.Verified)
    record.VerifiedAt = utc_now()
    db.commit()
    return record
