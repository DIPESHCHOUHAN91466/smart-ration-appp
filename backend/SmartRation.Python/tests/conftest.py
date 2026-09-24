from __future__ import annotations

import os
from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

LEGACY = "http://legacy.test"


def make_settings(tmp_path, **overrides) -> Settings:
    values = dict(
        database_url=f"sqlite:///{(tmp_path / 'unit.db').as_posix()}",
        legacy_api_url=LEGACY,
        cors_origins=["http://localhost:5173"],
        max_request_bytes=1024,
        log_level="WARNING",
    )
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def make_client(tmp_path) -> Callable[..., TestClient]:
    """Build an app whose fallback proxy talks to a fake C# API (`handler`)."""

    def build(handler=None, **overrides) -> TestClient:
        transport = httpx.MockTransport(handler) if handler else None
        app = create_app(make_settings(tmp_path, **overrides), legacy_transport=transport)
        return TestClient(app, raise_server_exceptions=False)

    return build


def live_database_url() -> str | None:
    """The real MySQL URL from backend/SmartRation.Python/.env, for integration tests."""
    try:
        return Settings().database_url
    except Exception:
        return os.environ.get("DATABASE_URL")
