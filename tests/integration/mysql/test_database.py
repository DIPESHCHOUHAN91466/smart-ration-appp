"""Connection-level checks: the server is reachable and configured correctly."""

from __future__ import annotations

import time

import pymysql
import pytest
from config import DB_CONFIG
from connection import UnsafeDatabaseError, check_safe, connect, describe


def test_select_1(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 AS ok")
        assert cur.fetchone() == {"ok": 1}


def test_connected_to_the_test_database(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT DATABASE() AS db, VERSION() AS version")
        row = cur.fetchone()
    assert row["db"] == DB_CONFIG["database"] and row["db"].endswith("_test")
    assert row["version"].startswith("8.")


def test_connection_is_utf8mb4_and_strict(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT @@character_set_connection AS cs, @@sql_mode AS mode, @@autocommit AS ac")
        row = cur.fetchone()
    assert row["cs"] == "utf8mb4"
    assert "STRICT_TRANS_TABLES" in row["mode"]
    assert row["ac"] == 0


def test_real_database_is_refused():
    with pytest.raises(UnsafeDatabaseError):
        check_safe({**DB_CONFIG, "database": "smartration"})


def test_description_never_contains_the_password(db_available):
    assert DB_CONFIG["password"] not in describe()


def test_wrong_password_fails_fast_and_cleanly(db_available):
    start = time.perf_counter()
    with pytest.raises(pymysql.err.OperationalError) as err:
        connect(password="definitely-not-the-password")
    assert err.value.args[0] == 1045
    assert "definitely-not-the-password" not in str(err.value)
    assert time.perf_counter() - start < 6


def test_unreachable_server_times_out(db_available):
    start = time.perf_counter()
    with pytest.raises(pymysql.err.OperationalError):
        connect(host="127.0.0.1", port=1)
    assert time.perf_counter() - start < 6
