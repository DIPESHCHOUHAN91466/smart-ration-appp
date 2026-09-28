"""Transactions: commit, rollback, isolation, and foreign keys with rollback."""

from __future__ import annotations

import pymysql
import pytest
from connection import PREFIX, connect, transaction


def count(cur) -> int:
    cur.execute("SELECT COUNT(*) AS n FROM test_users WHERE username LIKE %s", (PREFIX + "%",))
    return cur.fetchone()["n"]


def test_rollback_discards_everything(conn):
    with conn.cursor() as cur:
        for n in range(10):
            cur.execute("INSERT INTO test_users (username, full_name, email) VALUES (%s, %s, %s)", (f"{PREFIX}r{n}", "Rollback", f"r{n}@example.test"))
        assert count(cur) == 10                                # visible inside the transaction
        conn.rollback()
        assert count(cur) == 0                                 # gone after rollback


def test_uncommitted_rows_are_invisible_to_other_connections(conn):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO test_users (username, full_name, email) VALUES (%s, %s, %s)", (f"{PREFIX}iso", "Isolated", "iso@example.test"))
        other = connect()
        try:
            with other.cursor() as ocur:
                assert count(ocur) == 0                        # no dirty reads
            conn.commit()
            other.rollback()                                    # new snapshot
            with other.cursor() as ocur:
                assert count(ocur) == 1
        finally:
            other.close()


def test_context_manager_rolls_back_on_error(conn):
    with pytest.raises(RuntimeError), transaction() as t, t.cursor() as cur:
        cur.execute("INSERT INTO test_users (username, full_name, email) VALUES (%s, %s, %s)", (f"{PREFIX}cm", "CM", "cm@example.test"))
        raise RuntimeError("simulated failure mid-transaction")
    with conn.cursor() as cur:
        assert count(cur) == 0


@pytest.fixture
def parent_child(conn):
    """Two scratch tables with a foreign key (InnoDB temporary tables can't have FKs)."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS pytest_child, pytest_parent")
        cur.execute("CREATE TABLE pytest_parent (id INT PRIMARY KEY) ENGINE=InnoDB")
        cur.execute("CREATE TABLE pytest_child (id INT PRIMARY KEY, parent_id INT NOT NULL, "
                    "CONSTRAINT fk_pytest_child FOREIGN KEY (parent_id) REFERENCES pytest_parent(id) ON DELETE RESTRICT) ENGINE=InnoDB")
    yield conn
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS pytest_child, pytest_parent")


def test_foreign_key_violations_are_rejected(parent_child):
    conn = parent_child
    with conn.cursor() as cur:
        with pytest.raises(pymysql.err.IntegrityError) as err:
            cur.execute("INSERT INTO pytest_child VALUES (1, 999)")      # no such parent
        assert err.value.args[0] == 1452
        cur.execute("INSERT INTO pytest_parent VALUES (1)")
        cur.execute("INSERT INTO pytest_child VALUES (1, 1)")
        conn.commit()
        with pytest.raises(pymysql.err.IntegrityError) as err:
            cur.execute("DELETE FROM pytest_parent WHERE id = 1")      # still referenced
        assert err.value.args[0] == 1451
        conn.rollback()
        cur.execute("SELECT COUNT(*) AS n FROM pytest_parent")
        assert cur.fetchone()["n"] == 1
