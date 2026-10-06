"""Phase 1 configuration hardening: unknown environments, key reuse, wildcard CORS, the retired C# proxy and the
live API explorer are refused or off outside development."""

from __future__ import annotations

import pytest
from py_testkit import make_settings
from pydantic import ValidationError

from app.config.settings import Settings


def make(**overrides) -> Settings:
    values = dict(environment="production", data_mode="synthetic", database_url="sqlite://", jwt_secret_key="j" * 64,
                  qr_secret="q" * 48, demo_otp_enabled=False, sms_allow_mock_outside_development=True)
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize("typo", ["prod", "live", "dev", ""])
def test_an_unknown_environment_is_refused(typo):
    with pytest.raises(ValidationError, match="ENVIRONMENT must be one of"):
        make(environment=typo)


def test_environment_names_are_case_insensitive():
    assert make(environment=" Production ").is_production
    assert make(environment="staging").production_problems() == []      # staging gets the production rules
    assert not make(environment="staging").is_production                 # ... but no HSTS-only behaviour


def test_the_qr_secret_must_not_be_the_jwt_key_outside_development():
    same = "s" * 64
    assert any("QR_SECRET must differ" in p for p in make(qr_secret=same, jwt_secret_key=same).production_problems())
    assert make(environment="development", qr_secret=same, jwt_secret_key=same).production_problems() == []


def test_wildcard_cors_is_refused_outside_development():
    assert any("CORS_ORIGINS" in p for p in make(cors_origins="*").production_problems())
    assert make(cors_origins="https://ration.example.in").production_problems() == []


def test_the_retired_csharp_proxy_is_off_by_default():
    assert Settings(_env_file=None, database_url="sqlite://").legacy_api_url == ""


def test_api_docs_default_on_in_development_and_off_elsewhere():
    assert make(environment="development").docs_enabled
    assert not make().docs_enabled and not make(environment="staging").docs_enabled
    assert make(api_docs_enabled=True).docs_enabled                       # explicit opt-in still possible


def test_production_app_serves_no_api_explorer(tmp_path):
    from fastapi.testclient import TestClient

    from app.main import create_app
    settings = make_settings(tmp_path, environment="production", demo_otp_enabled=False,
                             sms_allow_mock_outside_development=True, legacy_api_url="")
    with TestClient(create_app(settings)) as client:
        for path in ("/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == 404, path
        assert client.get("/health/live").status_code == 200              # the API itself still answers
