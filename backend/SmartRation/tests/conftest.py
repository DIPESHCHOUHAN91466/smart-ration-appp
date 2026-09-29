from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient
from py_testkit import LEGACY, live_database_url, make_settings  # noqa: F401  (shared with test modules)

from app.main import create_app

pytest_plugins = ["ration_world"]  # the shared synthetic ration world (`env` fixture) for migrated-route tests


@pytest.fixture
def make_client(tmp_path) -> Callable[..., TestClient]:
    """Build an app whose fallback proxy talks to a fake C# API (`handler`)."""

    def build(handler=None, ai_handler=None, **overrides) -> TestClient:
        """`ai_handler` fakes the optional AI analytics service (it also sets a test URL and key)."""
        transport = httpx.MockTransport(handler) if handler else None
        ai_transport = httpx.MockTransport(ai_handler) if ai_handler else None
        if ai_handler:
            overrides = {"ai_service_url": "http://ai.test", "ai_service_api_key": "unit-test-ai-key", **overrides}
        app = create_app(make_settings(tmp_path, **overrides), legacy_transport=transport, ai_api_transport=ai_transport)
        return TestClient(app, raise_server_exceptions=False)

    return build


