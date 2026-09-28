"""Alembic revision helpers used by /health/database and the setup/verify scripts."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import get_engine

# backend/SmartRation/migrations (Alembic); alembic.ini points at the same folder.
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


@lru_cache
def alembic_head() -> str | None:
    """The newest Alembic revision shipped with this code."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    return ScriptDirectory.from_config(cfg).get_current_head()


def current_revision() -> str | None:
    """The revision the database is at; None if it isn't managed by Alembic (or is unreachable)."""
    try:
        with get_engine().connect() as conn:
            if "alembic_version" not in {t.lower() for t in inspect(conn).get_table_names()}:
                return None
            return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except SQLAlchemyError:
        return None
