"""Engine, session factory and the FastAPI session dependency."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings

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


def database_encryption() -> str:
    """How this app's connection to the database is protected: the TLS version (e.g. "TLSv1.3"), "none", "n/a" for an
    embedded SQLite file, or "unknown" when it can't be read. No host, user or certificate details."""
    engine = get_engine()
    if engine.dialect.name != "mysql":
        return "n/a"
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SHOW SESSION STATUS LIKE 'Ssl_version'")).first()
    except SQLAlchemyError:
        return "unknown"
    return (row[1] if row else "") or "none"


def database_is_reachable() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
