"""Passwords, JWT access tokens and refresh tokens — wire-compatible with the
C# API (JwtService / BCrypt), so a token issued by either backend is accepted
by the other during the side-by-side migration.

Access token (HS256): claims exactly as the C# JwtSecurityTokenHandler writes
them — sub, email, the long .NET claim-type URIs for name and role, jti,
rationShopId (string, shop owners only), exp, iss, aud. No iat/nbf.

Refresh token: base64 of 64 random bytes; only its SHA-256 (uppercase hex) is
stored, like the C# RefreshTokens.TokenHash.

Passwords: new hashes are Argon2id. Existing BCrypt hashes ($2a$/$2b$) keep
working and are upgraded after a successful login (the C# API verifies both).
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import Settings

NAME_CLAIM = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
ROLE_CLAIM = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
CLOCK_SKEW_SECONDS = 30  # same tolerance as the C# TokenValidationParameters

_argon2 = PasswordHasher()  # argon2id, library defaults (m=64 MiB, t=3, p=4)


def utc_now() -> datetime:
    """Naive UTC, the way EF Core stores DateTime in this database."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_utc(value: datetime) -> str:
    """ISO-8601 with 7 fractional digits and 'Z', matching .NET's DateTime(Kind=Utc) JSON."""
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f") + "0Z"


# ---------------------------------------------------------------- passwords

def hash_password(password: str) -> str:
    return _argon2.hash(password)


@dataclass(frozen=True)
class PasswordCheck:
    valid: bool
    needs_upgrade: bool


def verify_password(password: str, stored_hash: str) -> PasswordCheck:
    if not stored_hash:
        return PasswordCheck(False, False)
    if stored_hash.startswith("$argon2"):
        try:
            _argon2.verify(stored_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return PasswordCheck(False, False)
        return PasswordCheck(True, _argon2.check_needs_rehash(stored_hash))
    if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except ValueError:
            return PasswordCheck(False, False)
        return PasswordCheck(ok, ok)  # a valid BCrypt hash is always upgraded
    return PasswordCheck(False, False)  # unknown format: fail closed


# ---------------------------------------------------------------- access tokens

@dataclass(frozen=True)
class TokenUser:
    id: int
    email: str
    full_name: str
    role: str
    ration_shop_id: int | None


def create_access_token(user: TokenUser, settings: Settings) -> tuple[str, datetime]:
    expires_at = utc_now() + timedelta(minutes=settings.access_token_expire_minutes)
    claims = {
        "sub": str(user.id),
        "email": user.email,
        NAME_CLAIM: user.full_name,
        ROLE_CLAIM: user.role,
        "jti": str(uuid.uuid4()),
    }
    if user.ration_shop_id is not None:
        claims["rationShopId"] = str(user.ration_shop_id)
    claims |= {
        "exp": int(expires_at.replace(tzinfo=timezone.utc).timestamp()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    token = jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


class InvalidToken(Exception):
    pass


def decode_access_token(token: str, settings: Settings) -> dict:
    """Validates signature (HS256 only), issuer, audience and expiry."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],  # never trust the token's own alg header
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            leeway=CLOCK_SKEW_SECONDS,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidToken(type(exc).__name__) from exc


# ---------------------------------------------------------------- refresh tokens

def generate_refresh_token(settings: Settings) -> tuple[str, str, datetime]:
    raw = base64.b64encode(secrets.token_bytes(64)).decode("ascii")
    return raw, hash_token(raw), utc_now() + timedelta(days=settings.refresh_token_expire_days)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
