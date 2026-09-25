from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient
from py_testkit import live_database_url  # noqa: F401  (re-exported for older imports)

from app.core.config import Settings
from app.main import create_app

LEGACY = "http://legacy.test"


def make_settings(tmp_path, **overrides) -> Settings:
    values = dict(
        database_url=f"sqlite:///{(tmp_path / 'unit.db').as_posix()}",
        legacy_api_url=LEGACY,
        cors_origins=["http://localhost:5173"],
        max_request_bytes=1024,
        jwt_secret_key="unit-test-signing-key-0123456789abcdef-0123456789",
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


