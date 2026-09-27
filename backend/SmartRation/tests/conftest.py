from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient
from py_testkit import LEGACY, live_database_url, make_settings  # noqa: F401  (shared with test modules)

from app.main import create_app


@pytest.fixture
def make_client(tmp_path) -> Callable[..., TestClient]:
    """Build an app whose fallback proxy talks to a fake C# API (`handler`)."""

    def build(handler=None, **overrides) -> TestClient:
        transport = httpx.MockTransport(handler) if handler else None
        app = create_app(make_settings(tmp_path, **overrides), legacy_transport=transport)
        return TestClient(app, raise_server_exceptions=False)

    return build


