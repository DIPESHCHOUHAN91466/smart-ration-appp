"""Engine, session factory and the FastAPI session dependency."""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import MetaData, create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    # Same constraint names EF Core used (FK_<Table>_<PrincipalTable>_<Column>),
    # so a database created by Alembic is identical to the existing one.
    metadata = MetaData(naming_convention={"fk": "FK_%(table_name)s_%(referred_table_name)s_%(column_0_name)s"})


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def configure_database(database_url: str) -> None:
    """(Re)bind the engine; called by create_app with that app's settings."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = _build_engine(database_url)
    _session_factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def get_engine() -> Engine:
    if _engine is None:
        configure_database(get_settings().database_url)
    assert _engine is not None
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    if _session_factory is None:
        configure_database(get_settings().database_url)
    assert _session_factory is not None
    return _session_factory


def _build_engine(database_url: str) -> Engine:
    kwargs: dict = {"pool_pre_ping": True}
    if database_url.startswith("mysql"):
        # pool_recycle below MySQL's wait_timeout; short connect timeout so a
        # down database fails fast instead of hanging requests.
        kwargs.update(pool_recycle=1800, pool_size=10, max_overflow=10, connect_args={"connect_timeout": 5})
    return create_engine(database_url, **kwargs)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def database_is_reachable() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


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
