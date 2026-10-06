"""Shared helpers for the database scripts (run from backend/SmartRation)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alembic.config import Config  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402
from sqlalchemy import create_engine, inspect, text  # noqa: E402
from sqlalchemy.engine import Engine, make_url  # noqa: E402

import app.database.models  # noqa: E402,F401  (register tables)
from app.config.settings import get_settings  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.migrations import MIGRATIONS_DIR  # noqa: E402

EXPECTED_DATABASE = "smartration"
LEGACY_MARKER_TABLE = "__efmigrationshistory"  # created by the C# API's EF Core migrations
ALEMBIC_TABLE = "alembic_version"


def database_url() -> str:
    return get_settings().database_url


def safe_url(url: str) -> str:
    """URL with the password hidden, for printing."""
    return make_url(url).render_as_string(hide_password=True)


def engine() -> Engine:
    url = database_url()
    kwargs = {"connect_args": {"connect_timeout": 5}} if url.startswith("mysql") else {}
    return create_engine(url, pool_pre_ping=True, **kwargs)


def database_name(url: str) -> str:
    return make_url(url).database or ""


def alembic_config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    return cfg


def alembic_head() -> str:
    return ScriptDirectory.from_config(alembic_config()).get_current_head()


def current_revision(eng: Engine) -> str | None:
    with eng.connect() as conn:
        if ALEMBIC_TABLE not in {t.lower() for t in inspect(conn).get_table_names()}:
            return None
        query = f"SELECT version_num FROM {ALEMBIC_TABLE}"   # a module constant, never input
        # nosemgrep: python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text
        return conn.execute(text(query)).scalar()


def table_names(eng: Engine) -> set[str]:
    return {t.lower() for t in inspect(eng).get_table_names()}


def model_tables() -> set[str]:
    return {t.lower() for t in Base.metadata.tables}
