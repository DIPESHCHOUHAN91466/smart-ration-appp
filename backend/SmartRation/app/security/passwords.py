"""Password hashing. New hashes are Argon2id; existing BCrypt hashes ($2a$/$2b$) keep
working and are upgraded after a successful login (the C# API verifies both).
Unknown hash formats fail closed."""

from __future__ import annotations

from dataclasses import dataclass

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_argon2 = PasswordHasher()  # argon2id, library defaults (m=64 MiB, t=3, p=4)


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
