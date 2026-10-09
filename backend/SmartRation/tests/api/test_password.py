"""/api/auth/password/* — change (signed in) and reset with a code sent to the registered mobile (N12)."""

from __future__ import annotations

from datetime import timedelta

import bcrypt
import pytest
from sqlalchemy import func, select

from app.database.base import Base
from app.database.connection import get_engine, get_session_factory
from app.database.enums import OtpStatus
from app.database.models import AuditLog, PasswordResetCode, RationShop, RefreshToken, User
from app.security.passwords import verify_password
from app.utils.time import utc_now

OLD = "demo123"
NEW = "Kite-River-Lamp-42"
BCRYPT_OLD = bcrypt.hashpw(OLD.encode(), bcrypt.gensalt(rounds=4)).decode()


@pytest.fixture
def api(make_client):
    client = make_client(lambda r: None)
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        db.add(RationShop(Id=1, ShopName="S", ShopCode="S-1", Address="a", District="d", State="s", Latitude=0, Longitude=0,
                          IsActive=True, CreatedAt=utc_now()))
        db.add(User(Id=1, FullName="Rahul Patil", Email="rural@example.com", MobileNumber="9000000001", PasswordHash=BCRYPT_OLD,
                    Role=1, IsActive=True, CreatedAt=utc_now()))
        db.add(User(Id=2, FullName="Shop Owner", Email="shop@example.com", MobileNumber="9000000051", PasswordHash=BCRYPT_OLD,
                    Role=2, IsActive=True, CreatedAt=utc_now(), RationShopId=1))
        db.commit()
    return client


def session():
    return get_session_factory()()


def login(api, password, email="rural@example.com"):
    return api.post("/api/auth/login", json={"email": email, "password": password})


def bearer(tokens):
    return {"Authorization": f"Bearer {tokens['accessToken']}"}


def active_sessions(user_id=1):
    with session() as db:
        return db.scalar(select(func.count()).select_from(RefreshToken)
                         .where(RefreshToken.UserId == user_id, RefreshToken.RevokedAt.is_(None)))


def actions():
    with session() as db:
        return [a.Action for a in db.scalars(select(AuditLog).order_by(AuditLog.Id))]


# ---------------------------------------------------------------- change

def change(api, tokens, current=OLD, new=NEW):
    return api.post("/api/auth/password/change", headers=bearer(tokens), json={"currentPassword": current, "newPassword": new})


def test_change_keeps_this_device_signed_in_and_signs_out_every_other_one(api):
    here, elsewhere = login(api, OLD).json()["data"], login(api, OLD).json()["data"]
    r = change(api, here)
    assert r.status_code == 200 and r.json()["message"] == "Password changed"
    fresh = r.json()["data"]
    assert active_sessions() == 1                                                   # only the new session
    for old in (here, elsewhere):
        assert api.post("/api/auth/refresh", json={"refreshToken": old["refreshToken"]}).status_code == 401
    assert api.post("/api/auth/refresh", json={"refreshToken": fresh["refreshToken"]}).status_code == 200
    assert login(api, OLD).status_code == 401 and login(api, NEW).status_code == 200
    assert "PASSWORD_CHANGED" in actions()


def test_change_needs_a_signed_in_user(api):
    assert api.post("/api/auth/password/change", json={"currentPassword": OLD, "newPassword": NEW}).status_code == 401


def test_a_wrong_current_password_is_refused_and_counts_towards_the_lock(api):
    tokens = login(api, OLD).json()["data"]
    r = change(api, tokens, current="not-my-password")
    assert r.status_code == 400 and r.json()["errors"] == ["CurrentPassword: The current password is incorrect."]
    assert "LOGIN_FAILED" in actions()
    for _ in range(4):
        change(api, tokens, current="not-my-password")
    assert change(api, tokens).json()["errorCode"] == "ACCOUNT_TEMPORARILY_LOCKED"   # five failures: locked
    with session() as db:
        assert verify_password(OLD, db.get(User, 1).PasswordHash).valid               # nothing was changed


@pytest.mark.parametrize("new, message", [
    ("short", "NewPassword: The field NewPassword must be a string with a minimum length of 12 and a maximum length of 100."),
    ("password1234", "NewPassword: This password is too common. Choose a less predictable one."),
    ("rahul-patil-2026", 'NewPassword: Remove "rahul" (it comes from your name). '
                         "Do not build the password from your email, mobile number, name or the service's name."),
])
def test_weak_new_passwords_are_refused(api, new, message):
    r = change(api, login(api, OLD).json()["data"], new=new)
    assert r.status_code == 400 and r.json()["errors"] == [message]


def test_the_new_password_must_differ_from_the_current_one(api):
    tokens = change(api, login(api, OLD).json()["data"]).json()["data"]
    r = change(api, tokens, current=NEW, new=NEW)
    assert r.status_code == 400 and "different from the current one" in r.json()["errors"][0]


# ---------------------------------------------------------------- reset

def ask(api, mobile="9000000001"):
    return api.post("/api/auth/password/reset/request", json={"mobileNumber": mobile})


def reset(api, otp="123456", new=NEW, mobile="9000000001"):
    return api.post("/api/auth/password/reset/confirm", json={"mobileNumber": mobile, "otp": otp, "newPassword": new})


def codes():
    with session() as db:
        return db.scalars(select(PasswordResetCode).order_by(PasswordResetCode.Id)).all()


def test_reset_with_the_code_sets_the_password_and_signs_out_everywhere(api):
    signed_in = login(api, OLD).json()["data"]
    r = ask(api)
    assert r.status_code == 200 and r.json()["data"]["mobileMasked"] == "******0001"
    (code,) = codes()
    assert code.CodeHash != "123456" and len(code.CodeHash) == 64                 # only a hash is stored
    r = reset(api)
    assert r.status_code == 200 and r.json()["message"] == "Password changed. Please sign in with the new password."
    assert api.post("/api/auth/refresh", json={"refreshToken": signed_in["refreshToken"]}).status_code == 401
    assert login(api, OLD).status_code == 401 and login(api, NEW).status_code == 200
    assert reset(api).status_code == 401                                           # a code works once
    assert {"PASSWORD_RESET_REQUESTED", "PASSWORD_RESET"} <= set(actions())


def test_staff_accounts_can_reset_too(api):
    ask(api, "9000000051")
    assert reset(api, mobile="9000000051").status_code == 200
    assert login(api, NEW, "shop@example.com").status_code == 200


def test_an_unknown_number_gets_the_same_answer_and_no_code(api):
    known, unknown = ask(api).json(), ask(api, "9876543210").json()
    assert known["message"] == unknown["message"] and set(known["data"]) == set(unknown["data"])
    assert len(codes()) == 1
    r = reset(api, mobile="9876543210")
    assert r.status_code == 401 and r.json()["errorCode"] == "OTP_INVALID"


def test_three_wrong_codes_finish_the_code(api):
    ask(api)
    assert [reset(api, otp="000000").status_code for _ in range(3)] == [401] * 3
    assert reset(api).status_code == 401 and codes()[0].Status == OtpStatus.Failed
    assert login(api, OLD).status_code == 200


def test_a_weak_new_password_does_not_use_the_code_up(api):
    ask(api)
    assert reset(api, new="password1234").status_code == 400
    assert codes()[0].Status == OtpStatus.Pending
    assert reset(api).status_code == 200


def test_an_expired_code_is_refused(api):
    ask(api)
    with session() as db:
        db.scalar(select(PasswordResetCode)).ExpiresAt = utc_now() - timedelta(seconds=1)
        db.commit()
    assert reset(api).status_code == 401


def test_a_locked_account_gets_no_code_and_cannot_reset(api):
    ask(api)
    with session() as db:
        for _ in range(5):
            db.add(AuditLog(UserId=1, Action="LOGIN_FAILED", EntityName="User", Result="FAILED", CreatedAt=utc_now()))
        db.commit()
    assert reset(api).status_code == 401                                           # even the right code
    with session() as db:
        db.scalar(select(PasswordResetCode)).CreatedAt -= timedelta(minutes=1)
        db.commit()
    assert ask(api).status_code == 200 and len(codes()) == 1                        # no new code sent


def test_at_most_five_reset_codes_per_account_per_day(api):
    with session() as db:
        for i in range(5):
            t = utc_now() - timedelta(hours=2, minutes=i)
            db.add(PasswordResetCode(UserId=1, CodeHash="0" * 64, AttemptCount=0, MaxAttempts=3, Status=int(OtpStatus.Expired),
                                     CreatedAt=t, ExpiresAt=t + timedelta(minutes=5)))
        db.commit()
    assert ask(api).status_code == 200 and len(codes()) == 5
