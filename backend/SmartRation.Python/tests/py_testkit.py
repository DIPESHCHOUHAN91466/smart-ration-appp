"""Helpers shared by the Python backend's conftest and test modules.

A uniquely named module (not conftest) so tests can import it without the tests folder
being a package; works from this folder and from the repository root.
"""

from __future__ import annotations

import os

from app.core.config import Settings


def live_database_url() -> str | None:
    """The real MySQL URL from backend/SmartRation.Python/.env, for integration tests."""
    try:
        return Settings().database_url
    except Exception:
        return os.environ.get("DATABASE_URL")
