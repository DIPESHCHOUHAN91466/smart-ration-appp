"""Where the root-level MySQL tests connect, resolved from the project's ONE database configuration:

1. TEST_DATABASE_URL                       (the same variable the MySQL suite in backend/ and CI use)
2. DATABASE_URL in backend/SmartRation.Python/.env, with the database name swapped to
   smartration_test (exactly what backend/SmartRation.Python/scripts/test_database_url.py does)
3. legacy DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME (repository-root .env), for old setups

`SOURCE` says which one was used (never the password). Whatever the source, conftest refuses a
database whose name doesn't end in _test.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

from dotenv import dotenv_values, load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _from_url(url: str, database: str | None = None) -> dict:
    parts = urlsplit(url.replace("mysql+pymysql://", "mysql://", 1))
    return {
        "host": parts.hostname or "127.0.0.1",
        "port": parts.port or 3306,
        "user": unquote(parts.username or ""),
        "password": unquote(parts.password or ""),
        "database": database or parts.path.lstrip("/"),
        "charset": "utf8mb4",
    }


def _resolve() -> tuple[dict, str]:
    if os.getenv("TEST_DATABASE_URL"):
        return _from_url(os.environ["TEST_DATABASE_URL"]), "TEST_DATABASE_URL"
    backend_url = dotenv_values(ROOT / "backend" / "SmartRation.Python" / ".env").get("DATABASE_URL") or ""
    if backend_url.startswith("mysql"):
        return _from_url(backend_url, database="smartration_test"), "backend/SmartRation.Python/.env DATABASE_URL (database: smartration_test)"
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "smartration_app"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "smartration_test"),
        "charset": "utf8mb4",
    }, "legacy DB_* variables (repository-root .env)"


DB_CONFIG, SOURCE = _resolve()
