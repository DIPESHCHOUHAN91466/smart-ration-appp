"""JWT access tokens and refresh tokens — wire-compatible with the C# API
(JwtService), so a token issued by either backend is accepted by the other.
Passwords live in app.security.passwords.

Access token (HS256): claims exactly as the C# JwtSecurityTokenHandler writes
them — sub, email, the long .NET claim-type URIs for name and role, jti,
rationShopId (string, shop owners only), exp, iss, aud. No iat/nbf.

Refresh token: base64 of 64 random bytes; only its SHA-256 (uppercase hex) is
stored, like the C# RefreshTokens.TokenHash.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.config.settings import Settings
from app.utils.time import utc_now

NAME_CLAIM = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
ROLE_CLAIM = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
CLOCK_SKEW_SECONDS = 30  # same tolerance as the C# TokenValidationParameters


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
    claims: dict[str, str | int] = {
        "sub": str(user.id),
        "email": user.email,
        NAME_CLAIM: user.full_name,
        ROLE_CLAIM: user.role,
        "jti": str(uuid.uuid4()),
    }
    if user.ration_shop_id is not None:
        claims["rationShopId"] = str(user.ration_shop_id)
    claims |= {
        "exp": int(expires_at.replace(tzinfo=UTC).timestamp()),
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
