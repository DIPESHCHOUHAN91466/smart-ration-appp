"""Register / login / refresh / logout — port of the C# AuthService.

Same messages, status codes, audit actions and response shape. Differences,
all strictly safer and invisible to clients:
  * register is one transaction (C# saved in several steps);
  * refresh locks the token row (SELECT ... FOR UPDATE), so two concurrent
    refreshes with the same token can't both succeed;
  * new passwords are hashed with Argon2id, and BCrypt hashes are upgraded
    after a successful login (the C# API verifies both formats).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.core.errors import Conflict, Forbidden, Unauthorized
from app.database.enums import UserRole
from app.database.models import User
from app.repositories import refresh_tokens, users
from app.security.passwords import PasswordCheck, hash_password, verify_password
from app.security.tokens import TokenUser, create_access_token, generate_refresh_token, hash_token
from app.services import audit_service
from app.services.data_provider import get_data_provider
from app.utils.masking import mask_email
from app.utils.time import format_utc, utc_now

log = logging.getLogger("smartration.auth")


@dataclass(frozen=True)
class RequestContext:
    ip_address: str | None


def user_summary(user: User) -> dict:
    return {
        "id": user.Id,
        "fullName": user.FullName,
        "email": user.Email,
        "mobileNumber": user.MobileNumber,
        "role": UserRole(user.Role).name,
        "rationShopId": user.RationShopId,
    }


def _token_user(user: User) -> TokenUser:
    return TokenUser(user.Id, user.Email, user.FullName, UserRole(user.Role).name, user.RationShopId)


def _issue_tokens(db: Session, user: User, settings: Settings) -> dict:
    access, access_expires = create_access_token(_token_user(user), settings)
    raw_refresh, refresh_hash, refresh_expires = generate_refresh_token(settings)
    refresh_tokens.add(db, user.Id, refresh_hash, refresh_expires, utc_now())
    return {"accessToken": access, "refreshToken": raw_refresh, "accessTokenExpiresAt": format_utc(access_expires), "user": user_summary(user)}


def issue_session(db: Session, user: User, settings: Settings) -> dict:
    """Access + refresh tokens and the user summary, exactly as a password login returns them.
    For other ways of signing in (login_otp_service). Does not commit."""
    return _issue_tokens(db, user, settings)


def register(db: Session, settings: Settings, ctx: RequestContext, full_name: str, email: str, mobile: str, password: str) -> dict:
    email = email.strip().lower()
    if users.email_taken(db, email):
        raise Conflict("An account with this email already exists.")
    if users.mobile_taken(db, mobile):
        raise Conflict("An account with this mobile number already exists.")

    # Self-registration is ALWAYS a Rural User; privileged roles are never client-chosen.
    user = User(FullName=full_name.strip(), Email=email, MobileNumber=mobile.strip(), PasswordHash=hash_password(password),
                Role=int(UserRole.RuralUser), IsActive=True, CreatedAt=utc_now(), RationShopId=None)
    try:
        users.add(db, user)
        beneficiary = get_data_provider(settings.data_mode).provision_citizen(db, user)
        audit_service.record(db, user.Id, "REGISTER", "User", str(user.Id), ip_address=ctx.ip_address)
        response = _issue_tokens(db, user, settings)
        db.commit()
    except IntegrityError:
        # Lost a race with a simultaneous registration of the same email/mobile.
        db.rollback()
        raise Conflict("An account with this email already exists.") from None
    log.info("user registered", extra={"fields": {"user_id": user.Id, "beneficiary": beneficiary.BeneficiaryCode}})
    return response


def login(db: Session, settings: Settings, ctx: RequestContext, email: str, password: str) -> dict:
    email = email.strip().lower()
    user = users.by_email(db, email)
    check = verify_password(password, user.PasswordHash) if user else PasswordCheck(valid=False, needs_upgrade=False)

    if user is None or not check.valid:
        audit_service.record(db, user.Id if user else None, "LOGIN_FAILED", "User",
                             details=f"email={mask_email(email)}", result="FAILED", ip_address=ctx.ip_address)
        db.commit()
        raise Unauthorized("Invalid email or password.")

    if not user.IsActive:
        raise Forbidden("This account has been deactivated. Contact your ration shop or district office.")

    if check.needs_upgrade and settings.password_upgrade_to_argon2:
        user.PasswordHash = hash_password(password)  # BCrypt -> Argon2id, transparent to the user

    role = UserRole(user.Role).name
    audit_service.record(db, user.Id, "LOGIN", "User", str(user.Id), role=role, ip_address=ctx.ip_address)
    response = _issue_tokens(db, user, settings)
    db.commit()
    log.info("user logged in", extra={"fields": {"user_id": user.Id, "role": role, "hash_upgraded": check.needs_upgrade}})
    return response


def refresh(db: Session, settings: Settings, raw_refresh_token: str) -> dict:
    token = refresh_tokens.by_hash(db, hash_token(raw_refresh_token), for_update=True)
    now = utc_now()
    if token is None or token.RevokedAt is not None or token.ExpiresAt <= now:
        db.rollback()
        raise Unauthorized("Refresh token is invalid or has expired. Please log in again.")

    user = users.by_id(db, token.UserId)
    if user is None:  # unreachable while the FK holds; never issue a token for a missing user
        db.rollback()
        raise Unauthorized("Refresh token is invalid or has expired. Please log in again.")
    raw_new, new_hash, new_expires = generate_refresh_token(settings)
    token.RevokedAt = now
    token.ReplacedByTokenHash = new_hash
    refresh_tokens.add(db, token.UserId, new_hash, new_expires, now)
    access, access_expires = create_access_token(_token_user(user), settings)
    db.commit()
    return {"accessToken": access, "refreshToken": raw_new, "accessTokenExpiresAt": format_utc(access_expires), "user": user_summary(user)}


def logout(db: Session, ctx: RequestContext, raw_refresh_token: str) -> None:
    token = refresh_tokens.by_hash(db, hash_token(raw_refresh_token))
    if token is not None and token.RevokedAt is None:
        token.RevokedAt = utc_now()
        audit_service.record(db, token.UserId, "LOGOUT", "User", str(token.UserId), ip_address=ctx.ip_address)
        db.commit()
