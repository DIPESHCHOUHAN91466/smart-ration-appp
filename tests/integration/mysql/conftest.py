"""Fixtures for the root-level MySQL tests. Skips everything if the test database isn't configured
or reachable; refuses (fails loudly) if the database name doesn't end in _test. Where the settings
come from: see config.py (TEST_DATABASE_URL, then the backend's DATABASE_URL, then legacy DB_*)."""

from __future__ import annotations

import pymysql
import pytest
from config import DB_CONFIG, SOURCE
from connection import PREFIX, check_safe, connect, describe


@pytest.fixture(scope="session")
def db_available() -> None:
    if not DB_CONFIG["password"]:
        pytest.skip(f"no database password configured (source: {SOURCE})")
    check_safe()
    try:
        connect().close()
    except pymysql.err.OperationalError as exc:
        if exc.args[0] in (1044, 1045, 1049):  # denied / wrong password / no such database: a config error
            pytest.fail(f"MySQL test database misconfigured at {describe()}: error {exc.args[0]} "
                        f"(settings from {SOURCE})", pytrace=False)
        pytest.skip(f"MySQL test database not reachable at {describe()}: error {exc.args[0]}")


@pytest.fixture
def conn(db_available):
    """A connection with the test rows cleaned up before and after each test."""
    c = connect()
    _cleanup(c)
    try:
        yield c
    finally:
        c.rollback()
        _cleanup(c)
        c.close()


def _cleanup(c) -> None:
    with c.cursor() as cur:
        cur.execute("DELETE FROM test_users WHERE username LIKE %s", (PREFIX + "%",))
    c.commit()
