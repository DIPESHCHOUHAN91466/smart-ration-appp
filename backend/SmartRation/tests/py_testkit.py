"""Helpers shared by the Python backend's conftest and test modules.

A uniquely named module (not conftest) so tests can import it without the tests folder
being a package; works from this folder and from the repository root.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.config.settings import Settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]  # backend/SmartRation
REPO_ROOT = BACKEND_ROOT.parents[1]


def live_database_url() -> str | None:
    """The real MySQL URL from backend/SmartRation/.env, for integration tests."""
    try:
        return Settings().database_url
    except Exception:
        return os.environ.get("DATABASE_URL")


LEGACY = "http://legacy.test"


def make_settings(tmp_path, **overrides) -> Settings:
    values = dict(
        database_url=f"sqlite:///{(tmp_path / 'unit.db').as_posix()}",
        legacy_api_url=LEGACY,
        cors_origins=["http://localhost:5173"],
        max_request_bytes=1024,
        jwt_secret_key="unit-test-signing-key-0123456789abcdef-0123456789",
        qr_secret="unit-test-qr-secret-0123456789abcdef",  # test-only value
        log_level="WARNING",
        ai_service_url="",  # unit tests never depend on a running AI service
    )
    values.update(overrides)
    return Settings(_env_file=None, **values)
