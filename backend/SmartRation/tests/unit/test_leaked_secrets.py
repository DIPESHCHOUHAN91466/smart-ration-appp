"""Signing secrets that were once published in this repository's history are refused outside development."""

from __future__ import annotations

import hashlib

from app.config import settings as settings_module
from app.config.settings import LEAKED_SECRET_SHA256, Settings

STAND_IN = "stand-in-for-a-published-secret-0123456789abcdef"   # not a real secret; its fingerprint is added below


def make(**overrides) -> Settings:
    values = dict(environment="production", data_mode="synthetic", database_url="sqlite://", jwt_secret_key="j" * 64,
                  qr_secret="q" * 48, demo_otp_enabled=False, sms_allow_mock_outside_development=True)
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_the_two_published_fingerprints_are_listed():
    assert len(LEAKED_SECRET_SHA256) == 2 and all(len(h) == 64 for h in LEAKED_SECRET_SHA256)


def test_a_published_secret_is_refused_in_production_but_tolerated_in_development(monkeypatch):
    monkeypatch.setattr(settings_module, "LEAKED_SECRET_SHA256", {hashlib.sha256(STAND_IN.encode()).hexdigest()})
    assert make().production_problems() == []
    qr = make(qr_secret=STAND_IN).production_problems()
    jwt = make(jwt_secret_key=STAND_IN).production_problems()
    assert any(p.startswith("QR_SECRET is a value that was published") for p in qr)
    assert any(p.startswith("JWT_SECRET_KEY is a value that was published") for p in jwt)
    assert STAND_IN not in " ".join(qr + jwt)                    # the message never repeats the secret
    assert make(environment="development", qr_secret=STAND_IN).production_problems() == []
