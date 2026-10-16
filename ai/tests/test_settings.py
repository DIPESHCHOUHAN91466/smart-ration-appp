"""Configuration loading: defaults, overrides and refusal to start without secrets."""

from __future__ import annotations

import pytest

from ai.api.main import create_app
from ai.configs.settings import load_settings

from ai_testkit import API_KEY


@pytest.fixture
def env(monkeypatch):
    # Start from a known state: ai/.env (if any) was loaded at import time.
    for name in ["SMARTRATION_AI_DB_URL", "SMARTRATION_AI_API_KEY", "FORECAST_DAYS", "LOG_LEVEL"]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SMARTRATION_AI_DB_URL", "sqlite://")
    monkeypatch.setenv("SMARTRATION_AI_API_KEY", API_KEY)
    return monkeypatch


def test_defaults_when_optional_settings_are_unset(env):
    s = load_settings()
    assert s.forecast_default_horizon_days == 7
    assert s.shop_utc_offset_minutes == 330 and s.log_level == "INFO"


def test_empty_value_falls_back_to_default(env):
    env.setenv("FORECAST_DAYS", "")
    assert load_settings().forecast_default_horizon_days == 7


def test_forecast_days_override(env):
    env.setenv("FORECAST_DAYS", "14")
    assert load_settings().forecast_default_horizon_days == 14


def test_missing_database_url_is_refused(env):
    env.delenv("SMARTRATION_AI_DB_URL")
    with pytest.raises(RuntimeError, match="SMARTRATION_AI_DB_URL"):
        load_settings()


def test_short_api_key_is_refused(env):
    env.setenv("SMARTRATION_AI_API_KEY", "too-short")
    with pytest.raises(RuntimeError, match="at least 24"):
        load_settings()


def test_create_app_without_settings_refuses_missing_configuration(env):
    env.delenv("SMARTRATION_AI_API_KEY")
    with pytest.raises(RuntimeError, match="SMARTRATION_AI_API_KEY"):
        create_app()
