"""Daily limits on shop-counter one-time codes (2026-10-17, Phase 3 Q2).

OTP_COUNTER_DAILY_LIMIT per citizen (all shops together) and OTP_COUNTER_SHOP_DAILY_LIMIT per shop account, per Indian
calendar day; counted from the stored codes, so they survive restarts and hold across instances (the concurrent
case runs on MySQL: tests/integration/mysql_suite/test_10_collection_concurrency.py). The usual cool-down is set to 0
here so the limits themselves can be exercised; the demo OTP is development-only, as everywhere in these tests."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from ration_world import book, session
from sqlalchemy import select

import app.utils.time as clock
from app.core.errors import ApiError
from app.database.models import AuditLog, Beneficiary, User
from app.services import otp_service

LIMITS = {"otp_resend_cooldown_seconds": 0, "otp_counter_daily_limit": 3, "otp_counter_shop_daily_limit": 50}
CITIZEN = "9000000001"


def _ask(env, headers=None, mobile=CITIZEN):
    return env["client"].post("/api/verification/otp/request", headers=headers or env["shop"], json={"mobileNumber": mobile})


def _beneficiary_id() -> int:
    with session() as db:
        return db.scalar(select(Beneficiary.Id).join(User, User.Id == Beneficiary.UserId).where(User.MobileNumber == CITIZEN))


def _pin(monkeypatch, utc: datetime) -> None:
    for module in (clock, otp_service):
        monkeypatch.setattr(module, "utc_now", lambda: utc)


@pytest.mark.parametrize("env", [LIMITS], indirect=True)
def test_the_fourth_code_of_the_day_is_refused_without_naming_the_number(env):
    book(env)
    assert [_ask(env).status_code for _ in range(3)] == [200, 200, 200]   # legitimate retries within the limit
    r = _ask(env)
    assert r.status_code == 429 and r.json()["errorCode"] == "OTP_DAILY_LIMIT"
    assert CITIZEN not in r.text and CITIZEN[-4:] not in r.json()["message"]
    with session() as db:                                                    # audited, without the number
        row = db.scalar(select(AuditLog).where(AuditLog.Action == "COUNTER_OTP_LIMIT"))
        assert row is not None and row.Result == "BLOCKED" and CITIZEN not in (row.Details or "")


@pytest.mark.parametrize("env", [LIMITS], indirect=True)
def test_an_unknown_number_still_gets_the_usual_answer_after_the_limit(env):
    book(env)
    for _ in range(3):
        _ask(env)
    unknown = _ask(env, mobile="9000000099")
    assert unknown.status_code == 404 and unknown.json()["message"] == otp_service.NOT_SERVED   # nothing about registration


@pytest.mark.parametrize("env", [LIMITS], indirect=True)
def test_another_shop_cannot_add_codes_beyond_the_citizens_limit(env):
    book(env)
    settings = env["client"].app.state.settings
    ben = _beneficiary_id()
    with session() as db:
        otp_service.request(db, settings, ben, 50)                         # shop 1
        otp_service.request(db, settings, ben, 50)
        otp_service.request(db, settings, ben, 51)                         # shop 2: counts towards the same limit
        with pytest.raises(ApiError) as refused:
            otp_service.request(db, settings, ben, 51)
    assert refused.value.status_code == 429 and refused.value.error_code == "OTP_DAILY_LIMIT"


@pytest.mark.parametrize("env", [LIMITS], indirect=True)
def test_the_citizens_own_sign_in_codes_do_not_use_up_the_counter_limit(env):
    book(env)
    for _ in range(3):                                                       # the citizen signs in with codes 3 times
        r = env["client"].post("/api/auth/otp/request", json={"mobileNumber": CITIZEN})
        assert r.status_code == 200, r.text
    assert _ask(env).status_code == 200                                      # the counter can still send one


@pytest.mark.parametrize("env", [LIMITS], indirect=True)
def test_the_limit_resets_at_midnight_in_india(env, monkeypatch):
    book(env)
    settings = env["client"].app.state.settings
    ben = _beneficiary_id()
    day = datetime(2026, 10, 16, 18, 20)                                    # 16 Oct 23:50 IST
    _pin(monkeypatch, day)
    with session() as db:
        for _ in range(3):
            otp_service.request(db, settings, ben, 50)
        _pin(monkeypatch, day + timedelta(minutes=9))                      # 23:59 IST: same Indian day
        with pytest.raises(ApiError):
            otp_service.request(db, settings, ben, 50)
        _pin(monkeypatch, day + timedelta(minutes=20))                     # 00:10 IST on the 17th (UTC still the 16th)
        assert otp_service.request(db, settings, ben, 50).Id


@pytest.mark.parametrize("env", [{**LIMITS, "otp_counter_daily_limit": 10, "otp_counter_shop_daily_limit": 2}], indirect=True)
def test_a_shop_account_has_its_own_daily_limit(env):
    book(env)
    assert [_ask(env).status_code for _ in range(2)] == [200, 200]
    r = _ask(env)
    assert r.status_code == 429 and r.json()["errorCode"] == "OTP_SHOP_DAILY_LIMIT"
