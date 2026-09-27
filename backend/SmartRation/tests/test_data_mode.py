"""DATA_MODE: synthetic providers now; real mode refused until real integrations exist."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from py_testkit import make_settings

from app.data_providers import (
    BLOCKED,
    IntegrationNotAvailable,
    RealDataProvider,
    SyntheticDataProvider,
    check_data_mode,
    get_data_provider,
)
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_is_the_default_and_selects_the_synthetic_provider(tmp_path):
    assert make_settings(tmp_path).data_mode == "synthetic"
    assert isinstance(get_data_provider("synthetic"), SyntheticDataProvider)
    check_data_mode("synthetic")  # no error


def test_real_mode_is_blocked_at_startup(tmp_path):
    with pytest.raises(IntegrationNotAvailable, match=BLOCKED):
        create_app(make_settings(tmp_path, data_mode="real"))


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        check_data_mode("production")


def test_real_provider_never_falls_back_to_synthetic_data():
    with pytest.raises(IntegrationNotAvailable, match=BLOCKED):
        RealDataProvider().provision_citizen(None, None)  # type: ignore[arg-type]


def test_seed_script_refuses_in_real_mode(tmp_path):
    env = {"DATABASE_URL": f"sqlite:///{(tmp_path / 'x.db').as_posix()}", "DATA_MODE": "real",
           "JWT_SECRET_KEY": "unit-test-signing-key-0123456789abcdef-0123456789", "SYSTEMROOT": r"C:\Windows"}
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_database.py")], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 1 and "Refusing" in result.stdout


@pytest.mark.parametrize("ai_status,expected,overall", [(200, "healthy", "healthy"), (500, "unhealthy", "degraded")])
def test_health_reports_the_ai_service(tmp_path, ai_status, expected, overall):
    legacy = httpx.MockTransport(lambda r: httpx.Response(200, json={}))
    ai = httpx.MockTransport(lambda r: httpx.Response(ai_status, json={}))
    app = create_app(make_settings(tmp_path, ai_service_url="http://ai.test"), legacy_transport=legacy, ai_transport=ai)
    body = TestClient(app).get("/health").json()
    assert (body["aiService"], body["status"], body["dataMode"], body["chatbot"]) == (expected, overall, "synthetic", "healthy")
