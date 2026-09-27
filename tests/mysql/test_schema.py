"""Schema checks for the test database."""

from __future__ import annotations

import pytest

EXPECTED_TEST_USERS = {"id", "username", "full_name", "email", "mobile", "notes", "created_at", "updated_at"}

# The application's tables (created in smartration_test by the MySQL suite in
# backend/SmartRation/tests/mysql_suite via the real Alembic migration).
APP_TABLES = {"users", "beneficiaries", "families", "rationshops", "tokens", "timeslots", "inventory", "rationcollections"}


def tables(conn) -> dict[str, dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT TABLE_NAME AS name, ENGINE AS engine, TABLE_COLLATION AS collation "
                    "FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()")
        return {r["name"].lower(): r for r in cur.fetchall()}


def test_test_users_table_exists_with_expected_columns(conn):
    assert "test_users" in tables(conn)
    with conn.cursor() as cur:
        cur.execute("SHOW COLUMNS FROM test_users")
        columns = {r["Field"] for r in cur.fetchall()}
    assert EXPECTED_TEST_USERS <= columns


def test_test_users_has_a_primary_key(conn):
    with conn.cursor() as cur:
        cur.execute("SHOW KEYS FROM test_users WHERE Key_name = 'PRIMARY'")
        assert [r["Column_name"] for r in cur.fetchall()] == ["id"]


def test_every_table_is_innodb_utf8mb4(conn):
    bad = {n: (t["engine"], t["collation"]) for n, t in tables(conn).items()
           if t["engine"] != "InnoDB" or not t["collation"].startswith("utf8mb4")}
    assert bad == {}


def test_application_schema_if_present(conn):
    present = set(tables(conn))
    if not present & APP_TABLES:
        pytest.skip("application tables not created yet (run the backend MySQL suite once)")
    assert APP_TABLES <= present
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE CONSTRAINT_SCHEMA = DATABASE()")
        assert cur.fetchone()["n"] >= 24
        cur.execute("SELECT version_num FROM alembic_version")
        assert cur.fetchone()["version_num"]
