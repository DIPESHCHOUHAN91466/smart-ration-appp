"""Two-factor sign-in primitives: TOTP (RFC 6238, via pyotp), encryption of the stored secret, and the short-lived
token that carries a half-finished sign-in from the password step to the code step.

* The TOTP secret is stored encrypted (Fernet, AES-128-CBC + HMAC-SHA256) with a key derived from
  MFA_ENCRYPTION_KEY, so a copy of the database alone can't generate codes. Losing that key turns every
  two-factor account's codes unusable: keep it with the other secrets.
* A code is accepted for the current 30-second step or one step either side (clock drift), and never for a
  step at or before the last one accepted (a seen code can't be replayed).
* The pending-sign-in token is a JWT with its own audience, so it can never be used as an access token.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
import uuid
from datetime import UTC, timedelta

import jwt
import pyotp
from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import Settings
from app.utils.time import utc_now

ISSUER = "Smart Ration"
STEP_SECONDS = 30
MFA_AUDIENCE = "SmartRationHSD2C.Mfa"
PENDING_MINUTES = 5


class MfaUnavailable(Exception):
    """MFA_ENCRYPTION_KEY is not configured."""


def _fernet(settings: Settings) -> Fernet:
    key = settings.mfa_encryption_key.strip()
    if not key:
        raise MfaUnavailable()
    # Any long random string works (e.g. Render's generated values): derive the 32-byte Fernet key from it.
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(key.encode("utf-8")).digest()))


def new_secret() -> str:
    return pyotp.random_base32()   # 160 bits, as authenticator apps expect


def encrypt(settings: Settings, secret: str) -> str:
    return _fernet(settings).encrypt(secret.encode("ascii")).decode("ascii")


def decrypt(settings: Settings, stored: str) -> str | None:
    try:
        return _fernet(settings).decrypt(stored.encode("ascii")).decode("ascii")
    except InvalidToken:
        return None   # a different MFA_ENCRYPTION_KEY: unusable, never a crash


def provisioning_uri(secret: str, account: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=account, issuer_name=ISSUER)


def accepted_step(secret: str, code: str, last_step: int | None, now: float | None = None) -> int | None:
    """The 30-second step the code belongs to (current ±1), or None. Steps at or before `last_step` are refused."""
    code = (code or "").strip()
    if len(code) != 6 or not code.isdigit():
        return None
    totp = pyotp.TOTP(secret)
    current = int((time.time() if now is None else now) // STEP_SECONDS)
    for step in (current - 1, current, current + 1):
        if last_step is not None and step <= last_step:
            continue
        if secrets.compare_digest(totp.generate_otp(step), code):
            return step
    return None


# ---------------------------------------------------------------- pending sign-in token

def create_pending_token(user_id: int, settings: Settings) -> str:
    expires = utc_now() + timedelta(minutes=PENDING_MINUTES)
    claims = {"sub": str(user_id), "purpose": "mfa", "jti": str(uuid.uuid4()), "iss": settings.jwt_issuer,
              "aud": MFA_AUDIENCE, "exp": int(expires.replace(tzinfo=UTC).timestamp())}
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def read_pending_token(token: str, settings: Settings) -> int | None:
    """The user id of a valid, unexpired pending sign-in, else None."""
    try:
        claims = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm], audience=MFA_AUDIENCE,
                            issuer=settings.jwt_issuer, options={"require": ["exp", "iss", "aud", "sub"]})
    except jwt.PyJWTError:
        return None
    if claims.get("purpose") != "mfa":
        return None
    try:
        return int(claims["sub"])
    except (KeyError, ValueError):
        return None
