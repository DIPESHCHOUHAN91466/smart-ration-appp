"""Sign-in with a one-time code sent to a citizen's registered mobile number (Rural Users only).

Reuses otp_service's table, hashing and SMS sender. A sign-in code is an OtpVerifications row requested
by the citizen themself (RequestedByUserId == their own user id); the shop counter's codes are requested
by a shop owner and verified by row id, so neither kind can unlock the other.

Staff (shop owners, officials) keep password sign-in.

Privacy:
  * the request answer is the same whether or not the number is registered, so nobody can probe
    which numbers have accounts; a wrong number, an expired code and a wrong code also get one message;
  * the code itself is never logged or stored, only its SHA-256; numbers are logged masked.
"""

from __future__ import annotations

import logging
import re
import secrets
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.core.errors import Forbidden, ServiceUnavailable, Unauthorized
from app.core.validation import ValidationFailed
from app.database.enums import OtpStatus, UserRole
from app.database.models import Beneficiary, OtpVerification, User
from app.services import audit_service, auth_service, otp_service, verification_service
from app.services.auth_service import RequestContext
from app.utils.masking import mask_mobile
from app.utils.time import utc_now

log = logging.getLogger("smartration.auth")

INVALID_CODE = "The code is wrong or has expired. Please try again or ask for a new code."


def normalize_mobile(raw: str) -> str:
    """'98765 43210', '+91-9876543210', '09876543210' -> '9876543210' (how numbers are stored).
    Raises ValidationFailed for anything that is not a 10-digit Indian mobile number."""
    digits = re.sub(r"[\s\-()]", "", raw or "")
    if digits.startswith("+91"):
        digits = digits[3:]
    elif len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if not re.fullmatch(r"[6-9]\d{9}", digits):
        raise ValidationFailed(["MobileNumber: Enter a 10-digit mobile number."])
    return digits


def _citizen(db: Session, mobile: str) -> tuple[User, Beneficiary] | None:
    """The active Rural User with this number and their beneficiary record, or None."""
    row = db.execute(
        select(User, Beneficiary).join(Beneficiary, Beneficiary.UserId == User.Id)
        .where(User.MobileNumber == mobile, User.Role == int(UserRole.RuralUser)).limit(1)
    ).first()
    if row is None:
        return None
    user, beneficiary = row
    if not user.IsActive or not beneficiary.IsActive or beneficiary.IsBlocked:
        return None
    return user, beneficiary


def _pending_codes(db: Session, user: User, beneficiary: Beneficiary, *, lock: bool = False) -> list[OtpVerification]:
    q = select(OtpVerification).where(OtpVerification.BeneficiaryId == beneficiary.Id,
                                      OtpVerification.RequestedByUserId == user.Id,
                                      OtpVerification.Status == int(OtpStatus.Pending))
    return list(db.scalars(q.with_for_update() if lock else q))


def request_code(db: Session, settings: Settings, ctx: RequestContext, raw_mobile: str) -> dict:
    mobile = normalize_mobile(raw_mobile)
    answer = {
        "mobileMasked": mask_mobile(mobile),
        "expiresInSeconds": settings.otp_expiry_minutes * 60,
        "resendAfterSeconds": settings.otp_resend_cooldown_seconds,
        # Development demo mode only (the API refuses to start with it elsewhere), as at the shop counter.
        "demoOtpValue": settings.demo_otp_value if settings.demo_otp_enabled else None,
    }
    found = _citizen(db, mobile)
    if found is None:
        audit_service.record(db, None, "LOGIN_OTP_REQUESTED", "User", details=f"mobile={mask_mobile(mobile)}",
                             result="IGNORED", ip_address=ctx.ip_address)
        db.commit()
        return answer
    user, beneficiary = found
    if auth_service.is_locked(db, user.Id) or _sent_today(db, user, beneficiary) >= settings.otp_daily_send_limit:
        # Locked out, or this number already got today's codes: send nothing (no SMS bill, no new guesses), same answer.
        audit_service.record(db, user.Id, "LOGIN_OTP_REQUESTED", "User", str(user.Id), details=f"mobile={mask_mobile(mobile)}",
                             result="BLOCKED", ip_address=ctx.ip_address)
        db.commit()
        return answer

    now = utc_now()
    pending = _pending_codes(db, user, beneficiary)
    newest = max(pending, key=lambda o: o.CreatedAt, default=None)
    if newest is not None and (now - newest.CreatedAt).total_seconds() < settings.otp_resend_cooldown_seconds:
        return answer  # too soon: the code already sent still works
    for old in pending:
        old.Status = int(OtpStatus.Expired)  # only the newest sign-in code is valid

    code = settings.demo_otp_value if settings.demo_otp_enabled else f"{secrets.randbelow(1_000_000):06d}"
    record = OtpVerification(BeneficiaryId=beneficiary.Id, RequestedByUserId=user.Id, OtpHash=otp_service._hash(code),
                             AttemptCount=0, MaxAttempts=settings.otp_max_attempts, Status=int(OtpStatus.Pending),
                             CreatedAt=now, ExpiresAt=now + timedelta(minutes=settings.otp_expiry_minutes))
    db.add(record)
    db.commit()
    sent = otp_service.send_sms(settings, user.MobileNumber,
                                f"Your Smart Ration sign-in code is {code}. Valid for {settings.otp_expiry_minutes} minutes. "
                                "Never share it, not even with the ration shop.")
    if not sent.sent:
        record.Status = int(OtpStatus.Failed)  # an undeliverable code must not stay usable
        db.commit()
        raise ServiceUnavailable("Could not send the code right now. Please try again or sign in with your password.",
                                 "SMS_UNAVAILABLE")
    audit_service.record(db, user.Id, "LOGIN_OTP_REQUESTED", "User", str(user.Id), details=f"mobile={mask_mobile(mobile)}",
                         ip_address=ctx.ip_address)
    db.commit()
    return answer


def verify_code(db: Session, settings: Settings, ctx: RequestContext, raw_mobile: str, code: str) -> dict:
    mobile = normalize_mobile(raw_mobile)
    found = _citizen(db, mobile)
    record = None
    if found is not None:
        pending = _pending_codes(db, *found, lock=True)
        record = max(pending, key=lambda o: o.CreatedAt, default=None)

    if found is None or record is None:
        _failed(db, ctx, None, mobile)
        raise Unauthorized(INVALID_CODE, "OTP_INVALID")
    user, beneficiary = found
    if auth_service.is_locked(db, user.Id):
        # The sign-in lock (5 failures of either kind in 15 minutes) holds here too. The answer is the usual one,
        # so a lock never reveals that a number is registered.
        audit_service.record(db, user.Id, "LOGIN_LOCKED", "User", str(user.Id), details="method=otp", result="BLOCKED",
                             ip_address=ctx.ip_address)
        db.commit()
        raise Unauthorized(INVALID_CODE, "OTP_INVALID")

    if utc_now() > record.ExpiresAt:
        record.Status = int(OtpStatus.Expired)
        _failed(db, ctx, user.Id, mobile)
        raise Unauthorized(INVALID_CODE, "OTP_INVALID")
    if not secrets.compare_digest(otp_service._hash((code or "").strip()), record.OtpHash):
        record.AttemptCount += 1
        if record.AttemptCount >= record.MaxAttempts:
            record.Status = int(OtpStatus.Failed)  # three wrong tries: this code is finished
        _failed(db, ctx, user.Id, mobile)
        raise Unauthorized(INVALID_CODE, "OTP_INVALID")

    if not user.IsActive:  # deactivated between the request and now
        raise Forbidden("This account has been deactivated. Contact your ration shop or district office.")
    record.Status = int(OtpStatus.Verified)
    record.VerifiedAt = utc_now()
    verification_service.mobile_number_confirmed(db, beneficiary.Id)   # the code reached this number
    audit_service.record(db, user.Id, "LOGIN", "User", str(user.Id), details="method=otp",
                         role=UserRole.RuralUser.name, ip_address=ctx.ip_address)
    response = auth_service.issue_session(db, user, settings)
    db.commit()
    log.info("user logged in", extra={"fields": {"user_id": user.Id, "role": UserRole.RuralUser.name, "method": "otp"}})
    return response


def _sent_today(db: Session, user: User, beneficiary: Beneficiary) -> int:
    """Sign-in codes created for this citizen in the last 24 hours (any status)."""
    since = utc_now() - timedelta(days=1)
    return db.scalar(select(func.count()).select_from(OtpVerification).where(
        OtpVerification.BeneficiaryId == beneficiary.Id, OtpVerification.RequestedByUserId == user.Id,
        OtpVerification.CreatedAt >= since)) or 0


def _failed(db: Session, ctx: RequestContext, user_id: int | None, mobile: str) -> None:
    audit_service.record(db, user_id, "LOGIN_FAILED", "User", details=f"method=otp mobile={mask_mobile(mobile)}",
                         result="FAILED", ip_address=ctx.ip_address)
    db.commit()
