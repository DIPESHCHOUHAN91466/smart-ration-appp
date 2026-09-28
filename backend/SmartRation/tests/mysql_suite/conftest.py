"""MySQL test suite: runs ONLY against a dedicated test database.

    set TEST_DATABASE_URL=mysql+pymysql://smartration_app:<password>@localhost:3306/smartration_test?charset=utf8mb4
    .venv\\Scripts\\python -m pytest tests/mysql_suite -v

Safety: the database name must end in `_test`; anything else (including the real
`smartration`) makes every test in this folder refuse to run. Without TEST_DATABASE_URL the
whole folder is skipped, so the normal `pytest` run is unaffected.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (register tables)
from app.config.settings import Settings
from app.database import session as database
from app.database.base import Base
from app.database.migrations import MIGRATIONS_DIR
from app.main import create_app
from app.models import User
from app.models.enums import UserRole
from app.security.passwords import hash_password
from app.utils.time import utc_now
from mysql_suite.support import _REPORT, KEY, new_session, record_fixture  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_TABLES = {"rationitems", "rationschemes", "schemeentitlementitems", "rationshops", "inventory", "timeslots"}

_URL = os.environ.get("TEST_DATABASE_URL", "")


def _guard() -> str:
    if not _URL:
        pytest.skip("TEST_DATABASE_URL not set (see tests/mysql_suite/conftest.py)", allow_module_level=True)
    url = make_url(_URL)
    if not url.drivername.startswith("mysql"):
        pytest.exit("TEST_DATABASE_URL must be a MySQL URL.", returncode=2)
    if not (url.database or "").endswith("_test"):
        pytest.exit(f"Refusing to run: database '{url.database}' does not end in _test. "
                    "This suite writes and deletes data; point it at a dedicated test database.", returncode=2)
    return _URL


# ------------------------------------------------------------------ database

@pytest.fixture(scope="session")
def test_url() -> str:
    return _guard()


@pytest.fixture(scope="session")
def engine(test_url) -> Iterator[Engine]:
    """The app's own engine (same pool/charset settings as production), bound to the test DB,
    with the schema created by the real Alembic migration and synthetic reference data seeded."""
    from alembic import command
    from alembic.config import Config

    database.configure_database(test_url)
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.attributes["database_url"] = test_url
    command.upgrade(cfg, "head")

    sys.path.insert(0, str(ROOT / "scripts"))
    import seed_database  # noqa: E402

    eng = database.get_engine()
    with Session(eng) as db, db.begin():
        seed_database.seed(db)  # reference data only; no users (no SEED_* passwords set)
    yield eng
    eng.dispose()


def wipe(eng: Engine) -> None:
    """Delete every non-reference row (children first) and reset slot counters."""
    with eng.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            if table.name.lower() not in REFERENCE_TABLES:
                conn.execute(table.delete())
        conn.execute(text("UPDATE TimeSlots SET BookedCount = 0, Capacity = 2"))
        conn.execute(text("UPDATE RationShops SET IsActive = 1"))


@pytest.fixture
def db(engine) -> Iterator[Session]:
    """A clean database for each test, and a session on it."""
    wipe(engine)
    session = database.get_session_factory()()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def password_hash() -> str:
    # One real Argon2id hash reused for bulk ORM inserts (hashing 100 times would dominate timings).
    return hash_password("Synthetic-Pass-shared!")


@pytest.fixture
def make_user(password_hash) -> Callable[..., User]:
    def build(email: str, mobile: str, full_name: str = "Test Person", **kw) -> User:
        return User(FullName=full_name, Email=email, MobileNumber=mobile, PasswordHash=password_hash,
                    Role=int(UserRole.RuralUser), IsActive=True, CreatedAt=utc_now(), **kw)
    return build


# ------------------------------------------------------------------ HTTP API on the test DB

@pytest.fixture
def api(db, test_url) -> Iterator[TestClient]:
    settings = Settings(_env_file=None, database_url=test_url, legacy_api_url="", jwt_secret_key=KEY,
                        auth_rate_limit_per_minute=100_000, log_level="WARNING")
    with TestClient(create_app(settings), raise_server_exceptions=False) as client:
        yield client


# ------------------------------------------------------------------ performance report

@pytest.fixture
def record() -> Callable[[str, float, str], None]:
    return record_fixture()


def pytest_terminal_summary(terminalreporter):
    if not _REPORT:
        return
    terminalreporter.section("MySQL performance (this machine, this run)")
    for name, seconds, note in _REPORT:
        terminalreporter.write_line(f"  {name:<52} {seconds * 1000:9.1f} ms  {note}")
