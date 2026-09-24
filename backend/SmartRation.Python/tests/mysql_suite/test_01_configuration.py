"""Checklist: the MySQL server, the connection and the pool are configured as they should be."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool


def var(conn, name: str):
    return conn.execute(text(f"SELECT @@{name}")).scalar()


def test_server_is_mysql_8(engine):
    with engine.connect() as conn:
        assert str(var(conn, "version")).startswith("8.")


def test_connection_charset_is_utf8mb4(engine):
    """Client, connection and results must all be utf8mb4 (full Unicode incl. emoji)."""
    with engine.connect() as conn:
        for name in ("character_set_client", "character_set_connection", "character_set_results"):
            assert var(conn, name) == "utf8mb4", name
        assert str(var(conn, "collation_connection")).startswith("utf8mb4_")


def test_every_table_is_innodb_utf8mb4(engine):
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT TABLE_NAME, ENGINE, TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()"
        )).all()
    assert len(rows) >= 25
    bad = [r for r in rows if r.ENGINE != "InnoDB" or not r.TABLE_COLLATION.startswith("utf8mb4")]
    assert bad == []


def test_strict_mode_is_on(engine):
    """STRICT_TRANS_TABLES makes MySQL reject too-long values instead of silently truncating them."""
    with engine.connect() as conn:
        assert "STRICT_TRANS_TABLES" in var(conn, "sql_mode")


def test_transaction_isolation_and_autocommit(engine):
    with engine.connect() as conn:
        assert var(conn, "transaction_isolation") == "REPEATABLE-READ"
        assert var(conn, "autocommit") == 0  # the app commits explicitly, one transaction per request


def test_deadlock_detection_and_lock_timeout(engine):
    with engine.connect() as conn:
        assert var(conn, "innodb_deadlock_detect") == 1
        assert 1 <= var(conn, "innodb_lock_wait_timeout") <= 120


def test_pool_is_persistent_and_safe(engine):
    """Pooled ("persistent") connections: reused between requests, checked before use,
    recycled well before MySQL's wait_timeout closes them, and within max_connections."""
    pool = engine.pool
    assert isinstance(pool, QueuePool)
    assert pool._pre_ping is True                      # dead connections are replaced, not handed out
    assert pool._recycle == 1800
    with engine.connect() as conn:
        wait_timeout = var(conn, "wait_timeout")
        max_connections = var(conn, "max_connections")
    assert pool._recycle < wait_timeout
    assert pool.size() + pool._max_overflow <= max_connections // 2


def test_connections_are_reused(engine):
    with engine.connect() as conn:
        first = conn.execute(text("SELECT CONNECTION_ID()")).scalar()
    with engine.connect() as conn:
        second = conn.execute(text("SELECT CONNECTION_ID()")).scalar()
    assert first == second  # same pooled connection, no reconnect per query


def test_app_account_is_least_privilege(engine):
    with engine.connect() as conn:
        user = conn.execute(text("SELECT CURRENT_USER()")).scalar()
        grants = [r[0] for r in conn.execute(text("SHOW GRANTS"))]
    assert not user.startswith("root@")
    global_grants = [g for g in grants if " ON *.* " in g]
    assert all(g.startswith("GRANT USAGE ON *.*") for g in global_grants), global_grants


def test_multiple_statements_are_disabled(engine):
    """A stacked query can't be smuggled in: the driver refuses multi-statements."""
    with engine.connect() as conn, pytest.raises(SQLAlchemyError):
        conn.execute(text("SELECT 1; SELECT 2"))


def test_database_name_is_a_test_database(engine):
    with engine.connect() as conn:
        assert conn.execute(text("SELECT DATABASE()")).scalar().endswith("_test")
