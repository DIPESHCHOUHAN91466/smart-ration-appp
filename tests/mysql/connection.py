"""Connections for the root-level MySQL tests (tests/mysql).

Settings come from config.DB_CONFIG (TEST_DATABASE_URL, else the backend's DATABASE_URL pointed at
smartration_test, else legacy DB_* - see config.py). Only databases whose name ends in `_test` are allowed, so these tests can
never write to the real `smartration` database. The password is never printed.
"""

from __future__ import annotations

from contextlib import contextmanager

import pymysql
from config import DB_CONFIG

PREFIX = "pytest_"  # every row the tests create has a username starting with this


class UnsafeDatabaseError(RuntimeError):
    pass


def describe(config: dict | None = None) -> str:
    """user@host:port/database, without the password (safe for logs and test output)."""
    c = config or DB_CONFIG
    return f"{c['user']}@{c['host']}:{c['port']}/{c['database']}"


def check_safe(config: dict | None = None) -> None:
    c = config or DB_CONFIG
    if not str(c["database"]).endswith("_test"):
        raise UnsafeDatabaseError(f"Refusing to use '{c['database']}': the tests only run against a database ending in _test.")


def connect(**overrides) -> pymysql.connections.Connection:
    """A new connection with strict, predictable settings: utf8mb4, no autocommit, dict rows."""
    config = {**DB_CONFIG, **overrides}
    check_safe(config)
    return pymysql.connect(
        host=config["host"], port=config["port"], user=config["user"], password=config["password"],
        database=config["database"], charset="utf8mb4", autocommit=False, connect_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )


@contextmanager
def transaction():
    """Commit on success, roll back on any error, always close."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
