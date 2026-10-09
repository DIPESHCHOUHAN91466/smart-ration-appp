"""Change a password (signed in) and reset a forgotten one with a code sent to the registered mobile (any role).

Both end every other session of the account (all refresh tokens are revoked). Wrong current passwords and wrong
reset codes count as failed sign-ins, so the 5-in-15-minutes account lock (auth_service) covers them too.

Privacy, as for OTP sign-in: the reset request answers the same whether or not the number is registered, a wrong
number, an expired code and a wrong code get one message, and codes are never logged or stored (SHA-256 only).
"""

from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.core.errors import ServiceUnavailable, Unauthorized
from app.core.validation import ValidationFailed
from app.database.enums import OtpStatus
from app.database.models import PasswordResetCode, User
from app.repositories import refresh_tokens, users
from app.security import password_policy
from app.security.passwords import hash_password, verify_password
from app.security.rate_limit import TooManyRequests
from app.services import audit_service, auth_service, otp_service
from app.services.auth_service import RequestContext
from app.services.login_otp_service import normalize_mobile
from app.utils.masking import mask_mobile
from app.utils.time import utc_now

log = logging.getLogger("smartration.auth")

INVALID_RESET_CODE = "The code is wrong or has expired. Please try again or ask for a new code."
WRONG_CURRENT = "CurrentPassword: The current password is incorrect."


def _check_new_password(user: User, new_password: str, field: str = "NewPassword") -> None:
    weak = password_policy.problems(new_password, email=user.Email, mobile=user.MobileNumber, full_name=user.FullName)
    if not weak and verify_password(new_password, user.PasswordHash).valid:
        weak = ["Password: Choose a password different from the current one."]
    if weak:
        raise ValidationFailed([w.replace("Password:", f"{field}:", 1) for w in weak])


def _set_password(db: Session, user: User, new_password: str, action: str, ctx: RequestContext, details: str | None = None) -> int:
    user.PasswordHash = hash_password(new_password)
    ended = refresh_tokens.revoke_all_for_user(db, user.Id, utc_now())
    audit_service.record(db, user.Id, action, "User", str(user.Id), f"{details + '; ' if details else ''}sessions ended={ended}",
                         ip_address=ctx.ip_address)
    return ended


# ---------------------------------------------------------------- change (signed in)

def change(db: Session, settings: Settings, ctx: RequestContext, user_id: int, current_password: str, new_password: str) -> dict:
    user = users.by_id(db, user_id)
    if user is None or not user.IsActive:
        raise Unauthorized("Authentication required.")
    if auth_service.is_locked(db, user.Id):
        raise TooManyRequests("Too many failed sign-in attempts for this account. Please wait 15 minutes and try again.",
                              "ACCOUNT_TEMPORARILY_LOCKED")
    if not verify_password(current_password, user.PasswordHash).valid:
        audit_service.record(db, user.Id, "LOGIN_FAILED", "User", str(user.Id), "method=password-change", result="FAILED",
                             ip_address=ctx.ip_address)
        db.commit()
        raise ValidationFailed([WRONG_CURRENT])
    _check_new_password(user, new_password)
    _set_password(db, user, new_password, "PASSWORD_CHANGED", ctx)
    session = auth_service.issue_session(db, user, settings)   # this device stays signed in; every other one is signed out
    db.commit()
    log.info("password changed", extra={"fields": {"user_id": user.Id}})
    return session


# ---------------------------------------------------------------- reset (forgotten password)

def _account(db: Session, mobile: str) -> User | None:
    return db.scalar(select(User).where(User.MobileNumber == mobile, User.IsActive.is_(True)).order_by(User.Id).limit(1))


def _pending(db: Session, user_id: int, *, lock: bool = False) -> list[PasswordResetCode]:
    q = select(PasswordResetCode).where(PasswordResetCode.UserId == user_id, PasswordResetCode.Status == int(OtpStatus.Pending))
    return list(db.scalars(q.with_for_update() if lock else q))


def request_reset(db: Session, settings: Settings, ctx: RequestContext, raw_mobile: str) -> dict:
    mobile = normalize_mobile(raw_mobile)
    answer = {
        "mobileMasked": mask_mobile(mobile),
        "expiresInSeconds": settings.otp_expiry_minutes * 60,
        "resendAfterSeconds": settings.otp_resend_cooldown_seconds,
        "demoOtpValue": settings.demo_otp_value if settings.demo_otp_enabled else None,   # development only
    }
    user = _account(db, mobile)
    if user is None:
        audit_service.record(db, None, "PASSWORD_RESET_REQUESTED", "User", details=f"mobile={mask_mobile(mobile)}",
                             result="IGNORED", ip_address=ctx.ip_address)
        db.commit()
        return answer

    now = utc_now()
    sent_today = db.scalar(select(func.count()).select_from(PasswordResetCode).where(
        PasswordResetCode.UserId == user.Id, PasswordResetCode.CreatedAt >= now - timedelta(days=1))) or 0
    if auth_service.is_locked(db, user.Id) or sent_today >= settings.password_reset_daily_limit:
        audit_service.record(db, user.Id, "PASSWORD_RESET_REQUESTED", "User", str(user.Id), f"mobile={mask_mobile(mobile)}",
                             result="BLOCKED", ip_address=ctx.ip_address)
        db.commit()
        return answer
    pending = _pending(db, user.Id)
    newest = max(pending, key=lambda c: c.CreatedAt, default=None)
    if newest is not None and (now - newest.CreatedAt).total_seconds() < settings.otp_resend_cooldown_seconds:
        return answer  # too soon: the code already sent still works
    for old in pending:
        old.Status = int(OtpStatus.Expired)

    code = settings.demo_otp_value if settings.demo_otp_enabled else f"{secrets.randbelow(1_000_000):06d}"
    record = PasswordResetCode(UserId=user.Id, CodeHash=otp_service._hash(code), AttemptCount=0, MaxAttempts=settings.otp_max_attempts,
                               Status=int(OtpStatus.Pending), CreatedAt=now, ExpiresAt=now + timedelta(minutes=settings.otp_expiry_minutes))
    db.add(record)
    db.commit()
    sent = otp_service.deliver_code(settings, user, "Your Smart Ration password reset code",
                                    f"Your Smart Ration password reset code is {code}. Valid for {settings.otp_expiry_minutes} minutes. "
                                "If you did not ask for it, ignore this message. Never share it.")
    if not sent.sent:
        record.Status = int(OtpStatus.Failed)  # an undeliverable code must not stay usable
        db.commit()
        raise ServiceUnavailable("Could not send the code right now. Please try again later.", "SMS_UNAVAILABLE")
    audit_service.record(db, user.Id, "PASSWORD_RESET_REQUESTED", "User", str(user.Id), f"mobile={mask_mobile(mobile)}",
                         ip_address=ctx.ip_address)
    db.commit()
    return answer


def _failed(db: Session, ctx: RequestContext, user_id: int | None, mobile: str) -> None:
    audit_service.record(db, user_id, "LOGIN_FAILED", "User", details=f"method=password-reset mobile={mask_mobile(mobile)}",
                         result="FAILED", ip_address=ctx.ip_address)
    db.commit()


def confirm_reset(db: Session, ctx: RequestContext, raw_mobile: str, code: str, new_password: str) -> None:
    mobile = normalize_mobile(raw_mobile)
    user = _account(db, mobile)
    record = max(_pending(db, user.Id, lock=True), key=lambda c: c.CreatedAt, default=None) if user else None
    if user is None or record is None or auth_service.is_locked(db, user.Id):
        _failed(db, ctx, user.Id if user else None, mobile)
        raise Unauthorized(INVALID_RESET_CODE, "OTP_INVALID")
    if utc_now() > record.ExpiresAt:
        record.Status = int(OtpStatus.Expired)
        _failed(db, ctx, user.Id, mobile)
        raise Unauthorized(INVALID_RESET_CODE, "OTP_INVALID")
    if not secrets.compare_digest(otp_service._hash((code or "").strip()), record.CodeHash):
        record.AttemptCount += 1
        if record.AttemptCount >= record.MaxAttempts:
            record.Status = int(OtpStatus.Failed)
        _failed(db, ctx, user.Id, mobile)
        raise Unauthorized(INVALID_RESET_CODE, "OTP_INVALID")

    # The right code: a weak new password is refused WITHOUT using the code up, so the person can try another one.
    _check_new_password(user, new_password)
    record.Status = int(OtpStatus.Verified)
    record.UsedAt = utc_now()
    _set_password(db, user, new_password, "PASSWORD_RESET", ctx, f"mobile={mask_mobile(mobile)}")
    db.commit()
    log.info("password reset", extra={"fields": {"user_id": user.Id}})
