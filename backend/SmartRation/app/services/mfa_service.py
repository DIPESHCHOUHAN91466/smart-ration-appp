"""Two-factor sign-in (TOTP) for staff: shop owners, officials and admins turn it on themselves (opt-in).

    setup   (password)      -> a new secret for the authenticator app (not active yet)
    enable  (code)          -> active from now on: every password sign-in then needs a code
    disable (password+code) -> off
    verify  (pending token + code, after the password step) -> the session

Wrong passwords and wrong codes count as failed sign-ins (the 5-in-15-minutes account lock). A forgotten-password
reset does not turn two-factor sign-in off: the next sign-in still asks for a code.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.core.errors import ApiError, Conflict, Forbidden, Unauthorized
from app.core.validation import ValidationFailed
from app.database.enums import UserRole
from app.database.models import User
from app.repositories import users
from app.security import mfa
from app.security.passwords import verify_password
from app.security.rate_limit import TooManyRequests
from app.services import audit_service, auth_service
from app.services.auth_service import RequestContext
from app.utils.time import utc_now

log = logging.getLogger("smartration.auth")

STAFF_ROLES = (UserRole.ShopOwner, UserRole.GovernmentOfficial, UserRole.Admin)
WRONG_CODE = "Code: The code is wrong or has expired. Use the current code from your authenticator app."
WRONG_PASSWORD = "Password: The password is incorrect."
PENDING_INVALID = "The sign-in has expired. Please sign in again."


class MfaNotConfigured(ApiError):
    status_code = 503


def _not_configured() -> MfaNotConfigured:
    return MfaNotConfigured("Two-factor sign-in is not available on this server.", "MFA_NOT_CONFIGURED")


def _staff(db: Session, user_id: int) -> User:
    user = users.by_id(db, user_id)
    if user is None or not user.IsActive:
        raise Unauthorized("Authentication required.")
    if UserRole(user.Role) not in STAFF_ROLES:
        raise Forbidden("Two-factor sign-in is available for shop, official and admin accounts.")
    return user


def _guard(db: Session, user: User) -> None:
    if auth_service.is_locked(db, user.Id):
        raise TooManyRequests("Too many failed sign-in attempts for this account. Please wait 15 minutes and try again.",
                              "ACCOUNT_TEMPORARILY_LOCKED")


def _failed(db: Session, ctx: RequestContext, user: User, method: str) -> None:
    audit_service.record(db, user.Id, "LOGIN_FAILED", "User", str(user.Id), f"method={method}", result="FAILED",
                         ip_address=ctx.ip_address)
    db.commit()


def _check_password(db: Session, ctx: RequestContext, user: User, password: str) -> None:
    if not verify_password(password, user.PasswordHash).valid:
        _failed(db, ctx, user, "mfa-password")
        raise ValidationFailed([WRONG_PASSWORD])


def _secret(settings: Settings, user: User) -> str:
    secret = mfa.decrypt(settings, user.TotpSecret) if user.TotpSecret else None
    if secret is None:
        raise _not_configured()
    return secret


def status(db: Session, settings: Settings, user_id: int) -> dict:
    user = users.by_id(db, user_id)
    if user is None:
        raise Unauthorized("Authentication required.")
    return {"enabled": user.TotpEnabledAt is not None,
            "available": UserRole(user.Role) in STAFF_ROLES and bool(settings.mfa_encryption_key.strip())}


def setup(db: Session, settings: Settings, ctx: RequestContext, user_id: int, password: str) -> dict:
    user = _staff(db, user_id)
    _guard(db, user)
    _check_password(db, ctx, user, password)
    if user.TotpEnabledAt is not None:
        raise Conflict("Two-factor sign-in is already on. Turn it off first to set up a new device.", "MFA_ALREADY_ENABLED")
    secret = mfa.new_secret()
    try:
        user.TotpSecret = mfa.encrypt(settings, secret)
    except mfa.MfaUnavailable:
        raise _not_configured() from None
    user.TotpLastStep = None
    audit_service.record(db, user.Id, "MFA_SETUP_STARTED", "User", str(user.Id), ip_address=ctx.ip_address)
    db.commit()
    return {"secret": secret, "otpauthUri": mfa.provisioning_uri(secret, user.Email), "issuer": mfa.ISSUER}


def enable(db: Session, settings: Settings, ctx: RequestContext, user_id: int, code: str) -> dict:
    user = _staff(db, user_id)
    _guard(db, user)
    if user.TotpEnabledAt is not None:
        raise Conflict("Two-factor sign-in is already on.", "MFA_ALREADY_ENABLED")
    if not user.TotpSecret:
        raise Conflict("Start the set-up first.", "MFA_NOT_SET_UP")
    step = mfa.accepted_step(_secret(settings, user), code, None)
    if step is None:
        _failed(db, ctx, user, "mfa-enable")
        raise ValidationFailed([WRONG_CODE])
    user.TotpEnabledAt, user.TotpLastStep = utc_now(), step
    audit_service.record(db, user.Id, "MFA_ENABLED", "User", str(user.Id), ip_address=ctx.ip_address)
    db.commit()
    log.info("two-factor sign-in enabled", extra={"fields": {"user_id": user.Id}})
    return {"enabled": True, "available": True}


def disable(db: Session, settings: Settings, ctx: RequestContext, user_id: int, password: str, code: str) -> dict:
    user = _staff(db, user_id)
    _guard(db, user)
    if user.TotpEnabledAt is None:
        raise Conflict("Two-factor sign-in is not on.", "MFA_NOT_ENABLED")
    _check_password(db, ctx, user, password)
    step = mfa.accepted_step(_secret(settings, user), code, user.TotpLastStep)
    if step is None:
        _failed(db, ctx, user, "mfa-disable")
        raise ValidationFailed([WRONG_CODE])
    user.TotpSecret, user.TotpEnabledAt, user.TotpLastStep = None, None, None
    audit_service.record(db, user.Id, "MFA_DISABLED", "User", str(user.Id), ip_address=ctx.ip_address)
    db.commit()
    return {"enabled": False, "available": True}


def verify(db: Session, settings: Settings, ctx: RequestContext, pending_token: str, code: str) -> dict:
    user_id = mfa.read_pending_token(pending_token, settings)
    # Row lock: two requests with the same code can't both pass the replay check.
    user = db.get(User, user_id, with_for_update=True) if user_id is not None else None
    if user is None or not user.IsActive or user.TotpEnabledAt is None:
        raise Unauthorized(PENDING_INVALID, "MFA_PENDING_INVALID")
    _guard(db, user)
    step = mfa.accepted_step(_secret(settings, user), code, user.TotpLastStep)
    if step is None:
        _failed(db, ctx, user, "totp")
        raise Unauthorized(WRONG_CODE.removeprefix("Code: "), "MFA_CODE_INVALID")
    user.TotpLastStep = step
    role = UserRole(user.Role).name
    audit_service.record(db, user.Id, "LOGIN", "User", str(user.Id), "method=password+totp", role=role, ip_address=ctx.ip_address)
    session = auth_service.issue_session(db, user, settings)
    db.commit()
    log.info("user logged in", extra={"fields": {"user_id": user.Id, "role": role, "method": "password+totp"}})
    return session
