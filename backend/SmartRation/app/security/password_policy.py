"""Rules for a NEW password (registration, change, reset). Existing passwords keep working at sign-in.

NIST SP 800-63B style: length over composition. At least 12 characters, not a widely used password, and not
built from the person's own email, mobile number or name, or this service's name. No "one capital, one symbol"
rules: they make passwords harder to remember without making them harder to guess.

The common-password list ships with the code (common_passwords.txt) — no password ever leaves the server.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

MIN_LENGTH = 12
MAX_LENGTH = 100   # unchanged from the C# API contract
DIGITS, SYMBOLS = "0123456789", "!@#$%^&*.?_-"
SERVICE_WORDS = ("smartration", "rationmitra", "smart ration", "ration mitra")

TOO_SHORT = f"Password: Use at least {MIN_LENGTH} characters."
TOO_LONG = f"Password: Use at most {MAX_LENGTH} characters."
TOO_COMMON = "Password: This password is too common. Choose a less predictable one."
TOO_PERSONAL = "Password: Do not build the password from your email, mobile number, name or the service's name."
TOO_REPETITIVE = "Password: Avoid long runs of the same character or simple sequences."


@lru_cache(maxsize=1)
def _common() -> frozenset[str]:
    lines = (Path(__file__).with_name("common_passwords.txt")).read_text(encoding="utf-8").splitlines()
    return frozenset(line.strip() for line in lines if line.strip() and not line.startswith("#"))


def _personal_parts(email: str | None, mobile: str | None, full_name: str | None) -> list[str]:
    parts: list[str] = []
    if email:
        local = email.split("@", 1)[0].lower()
        parts += [local] if len(local) >= 4 else []
    if mobile:
        digits = re.sub(r"\D", "", mobile)
        parts += [digits[-10:]] if len(digits) >= 10 else []
    if full_name:
        parts += [w.lower() for w in re.split(r"\s+", full_name) if len(w) >= 4]
    return parts


def _repetitive(password: str) -> bool:
    if len(set(password)) <= 3:                          # "aaaaaaaaaaaa", "abababababab"
        return True
    lowered = password.lower()
    for seq in ("0123456789", "abcdefghijklmnopqrstuvwxyz", "qwertyuiop", "asdfghjkl"):
        for i in range(len(seq) - 7):                     # 8+ characters of a simple sequence
            if seq[i:i + 8] in lowered:
                return True
    return False


def problems(password: str, *, email: str | None = None, mobile: str | None = None, full_name: str | None = None) -> list[str]:
    """Why `password` is not acceptable as a new password ("Field: message" items); empty if it is."""
    if len(password) < MIN_LENGTH:
        return [TOO_SHORT]
    if len(password) > MAX_LENGTH:
        return [TOO_LONG]
    lowered = password.lower()
    # The password itself, without a trailing symbol ("password1234!"), or without padding digits/symbols.
    variants = {lowered, lowered.rstrip(SYMBOLS), lowered.strip(DIGITS + SYMBOLS)}
    if variants & _common():
        return [TOO_COMMON]
    squashed = re.sub(r"[\s._-]", "", lowered)
    if any(word.replace(" ", "") in squashed for word in SERVICE_WORDS) or \
            any(part and part in lowered for part in _personal_parts(email, mobile, full_name)):
        return [TOO_PERSONAL]
    if _repetitive(password):
        return [TOO_REPETITIVE]
    return []
