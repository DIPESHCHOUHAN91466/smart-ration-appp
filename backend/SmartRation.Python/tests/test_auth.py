"""/api/auth — behaviour, compatibility with C# tokens/hashes, and security."""

from __future__ import annotations

import base64
import json
from datetime import timedelta

import bcrypt
import jwt
import pytest
from sqlalchemy import func, select

from app.core.security import NAME_CLAIM, ROLE_CLAIM, TokenUser, create_access_token, hash_token, utc_now
from app.db.database import Base, get_engine, get_session_factory
from app.db.enums import UserRole
from app.db.models import (
    AadhaarVerification,
    AuditLog,
    Beneficiary,
    Family,
    MobileVerification,
    PassbookVerification,
    RationScheme,
    RationShop,
    RefreshToken,
    User,
)

KEY = "unit-test-signing-key-0123456789abcdef-0123456789"
BCRYPT_DEMO = bcrypt.hashpw(b"demo123", bcrypt.gensalt(rounds=4, prefix=b"2a")).decode()  # C#-style $2a$ hash


@pytest.fixture
def api(make_client):
    client = make_client(lambda r: None)  # auth routes never reach the proxy
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        db.add(RationShop(Id=1, ShopName="Satnavari", ShopCode="S-1", Address="a", District="d", State="s", Latitude=0, Longitude=0, IsActive=True, CreatedAt=utc_now()))
        db.add(RationScheme(Id=1, SchemeCode="DEMO-NFSA", Name="NFSA", Description="", IsActive=True))
        db.add(User(Id=1, FullName="Rahul Patil", Email="rural@example.com", MobileNumber="9000000001", PasswordHash=BCRYPT_DEMO, Role=1, IsActive=True, CreatedAt=utc_now()))
        db.add(User(Id=2, FullName="Shop Owner", Email="shop@example.com", MobileNumber="9000000051", PasswordHash=BCRYPT_DEMO, Role=2, IsActive=True, CreatedAt=utc_now(), RationShopId=1))
        db.add(User(Id=3, FullName="Gone", Email="inactive@example.com", MobileNumber="9000000052", PasswordHash=BCRYPT_DEMO, Role=1, IsActive=False, CreatedAt=utc_now()))
        db.commit()
    return client


def session():
    return get_session_factory()()


def claims(token: str) -> dict:
    payload = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


# ---------------------------------------------------------------- login


def test_login_returns_csharp_shaped_response_and_claims(api):
    r = api.post("/api/auth/login", json={"email": " Shop@Example.com ", "password": "demo123"})
    assert r.status_code == 200
    body = r.json()
    assert list(body) == ["success", "message", "data", "errors"] and body["message"] == "Login successful"
    d = body["data"]
    assert list(d) == ["accessToken", "refreshToken", "accessTokenExpiresAt", "user"]
    assert d["user"] == {"id": 2, "fullName": "Shop Owner", "email": "shop@example.com", "mobileNumber": "9000000051", "role": "ShopOwner", "rationShopId": 1}
    assert len(d["refreshToken"]) == 88 and d["accessTokenExpiresAt"].endswith("Z") and len(d["accessTokenExpiresAt"]) == 28
    c = claims(d["accessToken"])
    assert set(c) == {"sub", "email", NAME_CLAIM, ROLE_CLAIM, "jti", "rationShopId", "exp", "iss", "aud"}
    assert (c["sub"], c[ROLE_CLAIM], c["rationShopId"], c["iss"], c["aud"]) == ("2", "ShopOwner", "1", "SmartRationHSD2C", "SmartRationHSD2C.Clients")
    assert jwt.get_unverified_header(d["accessToken"]) == {"alg": "HS256", "typ": "JWT"}


def test_rural_user_token_has_no_shop_claim(api):
    d = api.post("/api/auth/login", json={"email": "rural@example.com", "password": "demo123"}).json()["data"]
    assert "rationShopId" not in claims(d["accessToken"]) and d["user"]["rationShopId"] is None


def test_bcrypt_hash_is_upgraded_to_argon2_and_still_works(api):
    assert api.post("/api/auth/login", json={"email": "rural@example.com", "password": "demo123"}).status_code == 200
    with session() as db:
        assert db.get(User, 1).PasswordHash.startswith("$argon2id$")
    assert api.post("/api/auth/login", json={"email": "rural@example.com", "password": "demo123"}).status_code == 200


def test_wrong_password_is_401_and_audited_with_masked_email(api):
    r = api.post("/api/auth/login", json={"email": "rural@example.com", "password": "nope"})
    assert r.status_code == 401
    assert r.json() == {"success": False, "message": "Invalid email or password.", "data": None, "errors": None}
    with session() as db:
        row = db.scalar(select(AuditLog).where(AuditLog.Action == "LOGIN_FAILED"))
        assert row.Details == "email=r***@example.com" and row.Result == "FAILED" and row.UserId == 1
        assert db.get(User, 1).PasswordHash == BCRYPT_DEMO  # never touched on failure


def test_unknown_user_and_inactive_user(api):
    assert api.post("/api/auth/login", json={"email": "ghost@example.com", "password": "demo123"}).status_code == 401
    r = api.post("/api/auth/login", json={"email": "inactive@example.com", "password": "demo123"})
    assert r.status_code == 403 and "deactivated" in r.json()["message"]


def test_successful_login_audited_with_role(api):
    api.post("/api/auth/login", json={"email": "shop@example.com", "password": "demo123"})
    with session() as db:
        row = db.scalar(select(AuditLog).where(AuditLog.Action == "LOGIN"))
        assert (row.UserId, row.Role, row.Result, row.EntityId) == (2, "ShopOwner", "SUCCESS", "2")


@pytest.mark.parametrize("body,errors", [
    ({}, ["Email: The Email field is required.", "Email: The Email field is not a valid e-mail address.", "Password: The Password field is required."]),
    ({"email": "not-an-email", "password": ""}, ["Email: The Email field is not a valid e-mail address.", "Password: The Password field is required."]),
])
def test_login_validation_messages_match_csharp(api, body, errors):
    r = api.post("/api/auth/login", json=body)
    assert r.status_code == 400
    assert r.json() == {"success": False, "message": "One or more validation errors occurred.", "data": None, "errors": errors}


def test_login_rate_limit_is_10_per_minute(api):
    codes = [api.post("/api/auth/login", json={"email": "x@y.z", "password": "bad"}).status_code for _ in range(12)]
    assert codes[:10] == [401] * 10 and codes[10:] == [429, 429]
    assert api.post("/api/auth/login", json={"email": "x@y.z", "password": "bad"}).json()["message"] == "Too many requests. Please wait a moment and try again."


# ---------------------------------------------------------------- register


def test_register_creates_rural_user_and_synthetic_beneficiary(api):
    r = api.post("/api/auth/register", json={"fullName": " Sunita More ", "email": "Sunita@Example.com", "mobileNumber": "9123456780", "password": "strongpass1"})
    assert r.status_code == 200 and r.json()["message"] == "Registration successful"
    user = r.json()["data"]["user"]
    assert user["role"] == "RuralUser" and user["email"] == "sunita@example.com" and user["fullName"] == "Sunita More"
    with session() as db:
        u = db.get(User, user["id"])
        assert u.PasswordHash.startswith("$argon2id$") and u.Role == UserRole.RuralUser
        b = db.scalar(select(Beneficiary).where(Beneficiary.UserId == u.Id))
        assert b.BeneficiaryCode == f"BEN-DEMO-{b.Id:04d}" and b.Gender == 3 and b.DataSource == "SYNTHETIC_DEMO"
        assert db.get(Family, b.FamilyId).FamilyCode == f"FAM-DEMO-{b.FamilyId:04d}"
        assert db.scalar(select(MobileVerification.MobileMasked).where(MobileVerification.BeneficiaryId == b.Id)) == "******6780"
        aadhaar = db.scalar(select(AadhaarVerification.AadhaarMasked).where(AadhaarVerification.BeneficiaryId == b.Id))
        assert aadhaar == f"XXXX-XXXX-{(b.Id * 6173) % 9000 + 1000}"  # masked synthetic reference only
        assert db.scalar(select(PassbookVerification.PassbookNumber).where(PassbookVerification.BeneficiaryId == b.Id)) == f"PB-DEMO-{b.Id:04d}"
        assert db.scalar(select(AuditLog.Action).where(AuditLog.UserId == u.Id)) == "REGISTER"


def test_register_ignores_client_supplied_role(api):
    r = api.post("/api/auth/register", json={"fullName": "Eve", "email": "eve@example.com", "mobileNumber": "9000000009", "password": "strongpass1", "role": "Admin"})
    assert r.json()["data"]["user"]["role"] == "RuralUser"


def test_register_duplicates_are_409(api):
    base = {"fullName": "Dup", "mobileNumber": "9111111111", "password": "strongpass1"}
    assert api.post("/api/auth/register", json={**base, "email": "rural@example.com"}).json()["message"] == "An account with this email already exists."
    r = api.post("/api/auth/register", json={**base, "email": "new@example.com", "mobileNumber": "9000000001"})
    assert r.status_code == 409 and r.json()["message"] == "An account with this mobile number already exists."


def test_register_validation_messages_match_csharp(api):
    r = api.post("/api/auth/register", json={"fullName": "A", "email": "x", "mobileNumber": "abc", "password": "short"})
    assert r.status_code == 400
    assert sorted(r.json()["errors"]) == sorted([
        "Email: The Email field is not a valid e-mail address.",
        "FullName: The field FullName must be a string with a minimum length of 2 and a maximum length of 150.",
        "Password: The field Password must be a string with a minimum length of 8 and a maximum length of 100.",
        "MobileNumber: The MobileNumber field is not a valid phone number.",
    ])


# ---------------------------------------------------------------- refresh / logout


def login_tokens(api, email="rural@example.com"):
    return api.post("/api/auth/login", json={"email": email, "password": "demo123"}).json()["data"]


def test_refresh_rotates_and_old_token_stops_working(api):
    first = login_tokens(api)
    r = api.post("/api/auth/refresh", json={"refreshToken": first["refreshToken"]})
    assert r.status_code == 200 and r.json()["message"] == "Token refreshed"
    second = r.json()["data"]
    assert second["refreshToken"] != first["refreshToken"]
    with session() as db:
        old = db.scalar(select(RefreshToken).where(RefreshToken.TokenHash == hash_token(first["refreshToken"])))
        assert old.RevokedAt is not None and old.ReplacedByTokenHash == hash_token(second["refreshToken"])
    reused = api.post("/api/auth/refresh", json={"refreshToken": first["refreshToken"]})
    assert reused.status_code == 401
    assert reused.json()["message"] == "Refresh token is invalid or has expired. Please log in again."


def test_expired_refresh_token_is_rejected(api):
    tokens = login_tokens(api)
    with session() as db:
        row = db.scalar(select(RefreshToken).where(RefreshToken.TokenHash == hash_token(tokens["refreshToken"])))
        row.ExpiresAt = utc_now() - timedelta(seconds=1)
        db.commit()
    assert api.post("/api/auth/refresh", json={"refreshToken": tokens["refreshToken"]}).status_code == 401


def test_refresh_tokens_are_stored_only_as_hashes(api):
    tokens = login_tokens(api)
    with session() as db:
        hashes = db.scalars(select(RefreshToken.TokenHash)).all()
    assert tokens["refreshToken"] not in hashes and hash_token(tokens["refreshToken"]) in hashes


def test_logout_revokes_and_is_idempotent(api):
    tokens = login_tokens(api)
    for _ in range(2):  # second call: already revoked, still 200 (same as C#)
        r = api.post("/api/auth/logout", json={"refreshToken": tokens["refreshToken"]})
        assert r.json() == {"success": True, "message": "Logged out", "data": None, "errors": None}
    assert api.post("/api/auth/refresh", json={"refreshToken": tokens["refreshToken"]}).status_code == 401
    with session() as db:
        assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.Action == "LOGOUT")) == 1
    assert api.post("/api/auth/logout", json={"refreshToken": "never-issued"}).status_code == 200


# ---------------------------------------------------------------- token validation (dependency)


def test_decode_rejects_tampering_wrong_key_and_alg_none():
    from app.core.config import Settings
    from app.core.security import InvalidToken, decode_access_token

    s = Settings(_env_file=None, database_url="sqlite://", jwt_secret_key=KEY)
    good, _ = create_access_token(TokenUser(1, "a@b.c", "A", "RuralUser", None), s)
    assert decode_access_token(good, s)["sub"] == "1"

    other = Settings(_env_file=None, database_url="sqlite://", jwt_secret_key="another-signing-key-0123456789abcdef")
    none_alg = jwt.encode({**claims(good)}, key="", algorithm="none") if hasattr(jwt, "encode") else good
    for bad in (good[:-2] + ("AA" if good[-2:] != "AA" else "BB"), create_access_token(TokenUser(1, "a", "A", "RuralUser", None), other)[0], none_alg):
        with pytest.raises(InvalidToken):
            decode_access_token(bad, s)
