"""app.security.passwords, app.security.tokens and app.utils.time as pure functions (no database, no HTTP)."""

from __future__ import annotations

from datetime import datetime

import bcrypt

from app.config.settings import Settings
from app.security.passwords import hash_password, verify_password
from app.security.tokens import NAME_CLAIM, ROLE_CLAIM, TokenUser, create_access_token, decode_access_token, generate_refresh_token, hash_token
from app.utils.time import format_utc, utc_now

SETTINGS = Settings(_env_file=None, database_url="sqlite://", jwt_secret_key="unit-test-signing-key-0123456789abcdef-0123456789")


def test_new_hashes_are_argon2id_and_verify():
    stored = hash_password("correct horse")
    assert stored.startswith("$argon2id$")
    assert verify_password("correct horse", stored).valid
    assert not verify_password("wrong", stored).valid


def test_the_same_password_hashes_differently_each_time():
    assert hash_password("same") != hash_password("same")  # random salt


def test_bcrypt_hashes_verify_and_ask_for_an_upgrade():
    stored = bcrypt.hashpw(b"demo123", bcrypt.gensalt(rounds=4, prefix=b"2a")).decode()
    check = verify_password("demo123", stored)
    assert check.valid and check.needs_upgrade
    assert not verify_password("demo124", stored).valid


def test_unknown_or_empty_hashes_fail_closed():
    for stored in ("", "plaintext", "$1$md5$whatever", "$argon2id$broken"):
        assert verify_password("anything", stored).valid is False


def test_access_token_claims_match_the_csharp_api():
    token, expires = create_access_token(TokenUser(7, "shop@example.com", "Shop Owner", "ShopOwner", 3), SETTINGS)
    claims = decode_access_token(token, SETTINGS)
    assert claims["sub"] == "7" and claims["email"] == "shop@example.com"
    assert claims[NAME_CLAIM] == "Shop Owner" and claims[ROLE_CLAIM] == "ShopOwner"
    assert claims["rationShopId"] == "3"
    assert claims["iss"] == SETTINGS.jwt_issuer and claims["aud"] == SETTINGS.jwt_audience
    assert "iat" not in claims and "nbf" not in claims
    assert expires > utc_now()


def test_refresh_tokens_are_random_and_only_the_hash_is_kept():
    raw1, hash1, _ = generate_refresh_token(SETTINGS)
    raw2, hash2, _ = generate_refresh_token(SETTINGS)
    assert raw1 != raw2 and hash1 != hash2
    assert hash1 == hash_token(raw1) and raw1 not in hash1
    assert len(hash1) == 64 and hash1 == hash1.upper()  # SHA-256, uppercase hex like the C# API


def test_time_helpers_match_dotnet_formats():
    assert utc_now().tzinfo is None  # naive UTC, as EF Core stores DateTime
    assert format_utc(datetime(2026, 9, 28, 10, 5, 3, 123456)) == "2026-09-28T10:05:03.1234560Z"
