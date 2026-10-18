"""One-time codes by e-mail (SMTP): the live demo has no SMS gateway, so password-reset, sign-in and counter codes
also go to the account's e-mail. smtplib is faked: nothing leaves the test."""

from __future__ import annotations

import re
import smtplib

import pytest
from sqlalchemy import select

from app.database.base import Base
from app.database.connection import get_engine, get_session_factory
from app.database.enums import OtpStatus
from app.database.models import PasswordResetCode, RationShop, User
from app.services import otp_service
from app.utils.time import utc_now
from tests.api.test_password import BCRYPT_OLD, NEW, OLD, login

SMTP = {"smtp_host": "smtp.test", "smtp_port": 587, "smtp_username": "sender@example.org", "smtp_password": "app-password"}


class FakeSmtp:
    """Records what would be sent; `fail` makes the server refuse."""
    sent: list = []
    calls: list = []
    fail = False

    def __init__(self, host, port, timeout):
        FakeSmtp.calls.append(("connect", host, port))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context=None):
        FakeSmtp.calls.append(("starttls",))

    def login(self, user, password):
        FakeSmtp.calls.append(("login", user))

    def send_message(self, message):
        if FakeSmtp.fail:
            raise smtplib.SMTPException("refused")
        FakeSmtp.sent.append(message)


@pytest.fixture(autouse=True)
def fake_smtp(monkeypatch):
    FakeSmtp.sent, FakeSmtp.calls, FakeSmtp.fail = [], [], False
    monkeypatch.setattr(otp_service.smtplib, "SMTP", FakeSmtp)


def client(make_client, **settings):
    api = make_client(lambda r: None, demo_otp_enabled=False, **settings)
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        db.add(RationShop(Id=1, ShopName="S", ShopCode="S-1", Address="a", District="d", State="s", Latitude=0, Longitude=0,
                          IsActive=True, CreatedAt=utc_now()))
        db.add(User(Id=1, FullName="Rahul Patil", Email="rural@example.com", MobileNumber="9000000001", PasswordHash=BCRYPT_OLD,
                    Role=1, IsActive=True, CreatedAt=utc_now()))
        db.commit()
    return api


def ask(api):
    return api.post("/api/auth/password/reset/request", json={"mobileNumber": "9000000001"})


def test_the_reset_code_arrives_by_email_and_works(make_client):
    api = client(make_client, **SMTP)
    assert ask(api).status_code == 200
    (mail,) = FakeSmtp.sent
    assert mail["To"] == "rural@example.com" and mail["Subject"] == "Your Smart Ration password reset code"
    assert ("starttls",) in FakeSmtp.calls and ("login", "sender@example.org") in FakeSmtp.calls
    code = re.search(r"\b(\d{6})\b", mail.get_content()).group(1)
    r = api.post("/api/auth/password/reset/confirm", json={"mobileNumber": "9000000001", "otp": code, "newPassword": NEW})
    assert r.status_code == 200, r.text
    assert login(api, OLD).status_code == 401 and login(api, NEW).status_code == 200


def test_without_smtp_no_email_is_attempted(make_client):
    api = client(make_client, sms_allow_mock_outside_development=False)
    assert ask(api).status_code == 200      # development: the mock SMS "sends"
    assert FakeSmtp.calls == []


def test_an_email_that_cannot_be_sent_cancels_the_code_when_there_is_no_sms_gateway(make_client):
    FakeSmtp.fail = True
    api = client(make_client, **SMTP)
    r = ask(api)
    assert r.status_code == 503 and r.json()["message"] == "Could not send the code right now. Please try again later."
    with get_session_factory()() as db:
        assert db.scalars(select(PasswordResetCode.Status)).all() == [int(OtpStatus.Failed)]   # never usable


def test_with_a_real_sms_gateway_a_failed_email_still_counts_as_sent(monkeypatch, make_client):
    FakeSmtp.fail = True
    monkeypatch.setattr(otp_service, "send_sms", lambda settings, phone, text: otp_service.SmsResult(True, "Http"))
    api = client(make_client, sms_provider="http", **SMTP)
    assert ask(api).status_code == 200


# ---------------------------------------------------------------- the live demo's configuration (2026-10-17, DEF-04)
# production + synthetic data + mock SMS (SMS_ALLOW_MOCK_OUTSIDE_DEVELOPMENT=true). Before the fix the mock counted as
# "sent" without SMTP: the API answered 200, the code stayed valid, and nobody ever received it.

LIVE_DEMO = {"environment": "production", "data_mode": "synthetic", "sms_allow_mock_outside_development": True}


def test_live_demo_without_smtp_refuses_code_requests_the_same_way_for_every_number(make_client):
    api = client(make_client, **LIVE_DEMO)
    answers = []
    for path in ("/api/auth/password/reset/request", "/api/auth/otp/request"):
        for mobile in ("9000000001", "9000000099"):                      # a real account and an unknown number
            r = api.post(path, json={"mobileNumber": mobile})
            answers.append((r.status_code, r.json()["errorCode"], r.json()["message"]))
    assert set(answers) == {(503, "SMS_UNAVAILABLE", otp_service.NO_DELIVERY)}   # identical: nothing to enumerate
    with get_session_factory()() as db:
        assert db.scalars(select(PasswordResetCode)).all() == []          # no code created that nobody could receive
    assert FakeSmtp.calls == []


def test_live_demo_with_smtp_sends_the_code_by_email(make_client):
    api = client(make_client, **LIVE_DEMO, **SMTP)
    assert ask(api).status_code == 200
    (mail,) = FakeSmtp.sent
    assert mail["To"] == "rural@example.com"


def test_live_demo_with_smtp_but_no_email_on_the_account_cancels_the_code(make_client):
    api = client(make_client, **LIVE_DEMO, **SMTP)
    with get_session_factory()() as db:
        db.get(User, 1).Email = ""
        db.commit()
    r = ask(api)
    assert r.status_code == 503 and r.json()["errorCode"] == "SMS_UNAVAILABLE"
    with get_session_factory()() as db:
        assert db.scalars(select(PasswordResetCode.Status)).all() == [int(OtpStatus.Failed)]   # never usable
    assert FakeSmtp.sent == []
