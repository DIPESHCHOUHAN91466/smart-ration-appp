"""Two-factor sign-in (TOTP) for staff (N12): set-up, sign-in challenge, replay and lock protection, turning it off."""

from __future__ import annotations

import time

import bcrypt
import pyotp
import pytest
from py_testkit import make_settings
from sqlalchemy import select

from app.database.base import Base
from app.database.connection import get_engine, get_session_factory
from app.database.models import AuditLog, RationShop, User
from app.security import mfa
from app.security.tokens import InvalidToken, decode_access_token
from app.utils.time import utc_now

KEY = "unit-test-mfa-encryption-key-0123456789abcdef"
HASH = bcrypt.hashpw(b"demo123", bcrypt.gensalt(rounds=4)).decode()


@pytest.fixture
def api(make_client):
    client = make_client(lambda r: None, mfa_encryption_key=KEY)
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        db.add(RationShop(Id=1, ShopName="S", ShopCode="S-1", Address="a", District="d", State="s", Latitude=0, Longitude=0,
                          IsActive=True, CreatedAt=utc_now()))
        db.add(User(Id=1, FullName="Officer", Email="officer@example.com", MobileNumber="9000000061", PasswordHash=HASH,
                    Role=3, IsActive=True, CreatedAt=utc_now()))
        db.add(User(Id=2, FullName="Rahul Patil", Email="rural@example.com", MobileNumber="9000000001", PasswordHash=HASH,
                    Role=1, IsActive=True, CreatedAt=utc_now()))
        db.commit()
    return client


def session():
    return get_session_factory()()


def login(api, email="officer@example.com", password="demo123", headers=None):
    return api.post("/api/auth/login", headers=headers or {}, json={"email": email, "password": password})


def bearer(api, email="officer@example.com"):
    return {"Authorization": f"Bearer {login(api, email).json()['data']['accessToken']}"}


def code_at(secret: str, steps_ahead: int = 0) -> str:
    return pyotp.TOTP(secret).generate_otp(int(time.time() // 30) + steps_ahead)


def turn_on(api) -> str:
    headers = bearer(api)
    secret = api.post("/api/auth/mfa/setup", headers=headers, json={"password": "demo123"}).json()["data"]["secret"]
    r = api.post("/api/auth/mfa/enable", headers=headers, json={"code": code_at(secret)})
    assert r.status_code == 200 and r.json()["data"] == {"enabled": True, "available": True}
    return secret


def test_set_up_gives_a_secret_for_the_app_and_stores_it_encrypted(api):
    headers = bearer(api)
    assert api.get("/api/auth/mfa/status", headers=headers).json()["data"] == {"enabled": False, "available": True}
    r = api.post("/api/auth/mfa/setup", headers=headers, json={"password": "demo123"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["otpauthUri"].startswith("otpauth://totp/Smart%20Ration:officer%40example.com?secret=")
    with session() as db:
        stored = db.get(User, 1)
        assert stored.TotpSecret and data["secret"] not in stored.TotpSecret      # encrypted at rest
        assert stored.TotpEnabledAt is None                                       # not on until a code confirms it
    assert login(api).json()["data"]["accessToken"]                               # sign-in unchanged so far


def test_set_up_needs_the_password(api):
    r = api.post("/api/auth/mfa/setup", headers=bearer(api), json={"password": "wrong"})
    assert r.status_code == 400 and r.json()["errors"] == ["Password: The password is incorrect."]


def test_citizens_cannot_use_it(api):
    r = api.post("/api/auth/mfa/setup", headers=bearer(api, "rural@example.com"), json={"password": "demo123"})
    assert r.status_code == 403


def test_with_it_on_the_password_alone_gives_no_session(api):
    secret = turn_on(api)
    r = login(api)
    data = r.json()["data"]
    assert r.status_code == 200 and data["mfaRequired"] is True and "accessToken" not in data
    assert data["mfaExpiresInSeconds"] == 300
    # The pending token is not an access token.
    assert api.get("/api/auth/mfa/status", headers={"Authorization": f"Bearer {data['mfaToken']}"}).status_code == 401
    done = api.post("/api/auth/mfa/verify", json={"mfaToken": data["mfaToken"], "code": code_at(secret, 1)})
    assert done.status_code == 200 and done.json()["data"]["accessToken"] and done.json()["data"]["refreshToken"]
    with session() as db:
        last = db.scalar(select(AuditLog.Details).where(AuditLog.Action == "LOGIN").order_by(AuditLog.Id.desc()).limit(1))
        assert last == "method=password+totp"


def test_a_code_cannot_be_used_twice(api):
    secret = turn_on(api)
    code = code_at(secret, 1)
    first = api.post("/api/auth/mfa/verify", json={"mfaToken": login(api).json()["data"]["mfaToken"], "code": code})
    assert first.status_code == 200
    again = api.post("/api/auth/mfa/verify", json={"mfaToken": login(api).json()["data"]["mfaToken"], "code": code})
    assert again.status_code == 401 and again.json()["errorCode"] == "MFA_CODE_INVALID"


def test_the_code_used_to_turn_it_on_cannot_sign_in(api):
    secret = turn_on(api)                                       # used the current step
    r = api.post("/api/auth/mfa/verify", json={"mfaToken": login(api).json()["data"]["mfaToken"], "code": code_at(secret)})
    assert r.status_code == 401


def test_wrong_codes_count_towards_the_account_lock(api):
    turn_on(api)
    token = login(api).json()["data"]["mfaToken"]
    for _ in range(5):
        assert api.post("/api/auth/mfa/verify", json={"mfaToken": token, "code": "000000"}).status_code == 401
    locked = api.post("/api/auth/mfa/verify", json={"mfaToken": token, "code": "000000"})
    assert locked.status_code == 429 and locked.json()["errorCode"] == "ACCOUNT_TEMPORARILY_LOCKED"


def test_forged_or_expired_pending_tokens_are_refused(api, make_client):
    secret = turn_on(api)
    for token in ("not-a-token", login(api).json()["data"]["mfaToken"] + "x"):
        r = api.post("/api/auth/mfa/verify", json={"mfaToken": token, "code": code_at(secret, 1)})
        assert r.status_code == 401 and r.json()["errorCode"] == "MFA_PENDING_INVALID"


def test_pending_tokens_carry_their_own_audience(tmp_path):
    settings = make_settings(tmp_path)
    token = mfa.create_pending_token(7, settings)
    assert mfa.read_pending_token(token, settings) == 7
    with pytest.raises(InvalidToken):
        decode_access_token(token, settings)                     # never accepted as an access token


def test_cookie_mode_sign_in_with_a_code_sets_the_cookie(api):
    secret = turn_on(api)
    pending = login(api, headers={"X-Auth-Mode": "cookie"}).json()["data"]["mfaToken"]
    r = api.post("/api/auth/mfa/verify", headers={"X-Auth-Mode": "cookie"}, json={"mfaToken": pending, "code": code_at(secret, 1)})
    assert r.status_code == 200 and r.json()["data"]["refreshToken"] is None and api.cookies.get("sr_refresh")


def test_turning_it_off_needs_password_and_code(api):
    secret = turn_on(api)
    pending = login(api).json()["data"]["mfaToken"]
    headers = {"Authorization": "Bearer " + api.post("/api/auth/mfa/verify",
                                                     json={"mfaToken": pending, "code": code_at(secret, 1)}).json()["data"]["accessToken"]}
    assert api.post("/api/auth/mfa/disable", headers=headers, json={"password": "wrong", "code": "123456"}).status_code == 400
    r = api.post("/api/auth/mfa/disable", headers=headers, json={"password": "demo123", "code": code_at(secret, -1)})
    assert r.status_code == 400                                  # a step at or before the last one used
    with session() as db:                                        # simulate the next step being reached
        db.get(User, 1).TotpLastStep -= 2
        db.commit()
    r = api.post("/api/auth/mfa/disable", headers=headers, json={"password": "demo123", "code": code_at(secret, 1)})
    assert r.status_code == 200 and r.json()["data"]["enabled"] is False
    assert login(api).json()["data"]["accessToken"]              # password sign-in again


def test_unavailable_without_an_encryption_key(make_client):
    client = make_client(lambda r: None)                        # MFA_ENCRYPTION_KEY not set
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        db.add(User(Id=1, FullName="Officer", Email="officer@example.com", MobileNumber="9000000061", PasswordHash=HASH,
                    Role=3, IsActive=True, CreatedAt=utc_now()))
        db.commit()
    headers = bearer(client)
    assert client.get("/api/auth/mfa/status", headers=headers).json()["data"] == {"enabled": False, "available": False}
    r = client.post("/api/auth/mfa/setup", headers=headers, json={"password": "demo123"})
    assert r.status_code == 503 and r.json()["errorCode"] == "MFA_NOT_CONFIGURED"


def test_a_key_shorter_than_32_or_reused_is_refused_outside_development(tmp_path):
    base = dict(environment="production", demo_otp_enabled=False, sms_allow_mock_outside_development=True)
    assert any("MFA_ENCRYPTION_KEY is too short" in p for p in make_settings(tmp_path, mfa_encryption_key="short", **base).production_problems())
    jwt_key = make_settings(tmp_path).jwt_secret_key
    assert any("must differ" in p for p in make_settings(tmp_path, mfa_encryption_key=jwt_key, **base).production_problems())
