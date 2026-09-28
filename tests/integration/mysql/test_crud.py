"""CRUD on test_users with prepared statements (%s placeholders), including edge cases."""

from __future__ import annotations

import pymysql
import pytest
from connection import PREFIX

SPECIAL = ["राहुल पाटील", "Zoë Ångström", "Sunita 🌾 Shinde", "O'Brien; DROP TABLE test_users; --", 'Say "hi"', "back\\slash", "%_wild"]


def insert(cur, n: int, full_name: str = "Test User", **kw) -> int:
    cur.execute(
        "INSERT INTO test_users (username, full_name, email, mobile, notes) VALUES (%s, %s, %s, %s, %s)",
        (f"{PREFIX}{n:03d}", full_name, kw.get("email", f"{PREFIX}{n:03d}@example.test"), kw.get("mobile", f"7{n:09d}"), kw.get("notes")),
    )
    return cur.lastrowid


def test_create_read_update_delete_100(conn):
    with conn.cursor() as cur:
        for n in range(100):
            insert(cur, n, SPECIAL[n % len(SPECIAL)])
        conn.commit()

        cur.execute("SELECT username, full_name FROM test_users WHERE username LIKE %s ORDER BY username", (PREFIX + "%",))
        rows = cur.fetchall()
        assert len(rows) == 100
        assert all(r["full_name"] == SPECIAL[i % len(SPECIAL)] for i, r in enumerate(rows))   # exact round trip

        cur.execute("UPDATE test_users SET notes = %s WHERE username LIKE %s", ("updated", PREFIX + "%"))
        assert cur.rowcount == 100
        cur.execute("DELETE FROM test_users WHERE username LIKE %s AND id %% 2 = 0", (PREFIX + "%",))
        conn.commit()

        cur.execute("SELECT COUNT(*) AS n, SUM(notes = 'updated') AS upd FROM test_users WHERE username LIKE %s", (PREFIX + "%",))
        row = cur.fetchone()
    assert 0 < row["n"] < 100 and row["upd"] == row["n"]


def test_batch_insert_with_executemany(conn):
    rows = [(f"{PREFIX}b{n:03d}", f"Batch {n}", f"{PREFIX}b{n:03d}@example.test", f"8{n:09d}") for n in range(100)]
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO test_users (username, full_name, email, mobile) VALUES (%s, %s, %s, %s)", rows)
        conn.commit()
        cur.execute("SELECT COUNT(*) AS n FROM test_users WHERE username LIKE %s", (PREFIX + "b%",))
        assert cur.fetchone()["n"] == 100


@pytest.mark.parametrize("payload", ["' OR '1'='1", "'; DROP TABLE test_users; --", "' UNION SELECT 1,2,3 -- ", "1' AND SLEEP(3) AND '1'='1"])
def test_injection_through_placeholders_is_inert(conn, payload):
    with conn.cursor() as cur:
        insert(cur, 1)
        conn.commit()
        cur.execute("SELECT id FROM test_users WHERE username = %s", (payload,))
        assert cur.fetchall() == ()
        cur.execute("SELECT COUNT(*) AS n FROM test_users WHERE username LIKE %s", (PREFIX + "%",))
        assert cur.fetchone()["n"] == 1                        # table intact, nothing deleted


def test_empty_values_and_null(conn):
    with conn.cursor() as cur:
        insert(cur, 2, full_name="", notes=None)
        conn.commit()
        cur.execute("SELECT full_name, notes FROM test_users WHERE username = %s", (f"{PREFIX}002",))
        assert cur.fetchone() == {"full_name": "", "notes": None}


def test_too_long_value_is_rejected_not_truncated(conn):
    with conn.cursor() as cur, pytest.raises(pymysql.err.DataError) as err:
        insert(cur, 3, full_name="x" * 256)                   # full_name is VARCHAR(255)
    assert err.value.args[0] == 1406
    conn.rollback()


def test_max_length_multibyte_value_fits(conn):
    with conn.cursor() as cur:
        insert(cur, 4, full_name="अ" * 255)                    # 255 characters, 765 bytes
        conn.commit()
        cur.execute("SELECT CHAR_LENGTH(full_name) AS c FROM test_users WHERE username = %s", (f"{PREFIX}004",))
        assert cur.fetchone()["c"] == 255
