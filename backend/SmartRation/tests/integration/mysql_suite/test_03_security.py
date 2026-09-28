"""Security: SQL injection attempts are inert because every query uses bound parameters.

Payloads are only ever sent to the dedicated _test database. Each test checks both that the
attack failed AND that the database is unchanged afterwards.
"""

from __future__ import annotations

import time

import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.dialects import mysql

from app.database.models import User
from mysql_suite.sample_data import INJECTION_PAYLOADS


@pytest.fixture
def victims(db, make_user):
    """Two ordinary users an injection would try to read, change or delete."""
    db.add_all([make_user("victim1@example.test", "7100000001", "Victim One"),
                make_user("victim2@example.test", "7100000002", "Victim Two")])
    db.commit()
    return db


def database_unchanged(db) -> None:
    db.expire_all()
    assert "users" in {t.lower() for t in inspect(db.get_bind()).get_table_names()}
    assert db.scalar(select(func.count()).select_from(User)) == 2
    assert db.scalar(select(func.max(User.Role))) == 1  # nobody escalated to Admin (4)


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_login_injection_is_rejected(api, victims, payload):
    for body in ({"email": payload, "password": payload},
                 {"email": "victim1@example.test", "password": payload},
                 {"email": f"x@{payload}", "password": "anything-long"}):
        start = time.perf_counter()
        r = api.post("/api/auth/login", json=body)
        assert r.status_code in (400, 401), (payload, r.status_code)
        assert "accessToken" not in r.text
        assert time.perf_counter() - start < 3  # SLEEP()/BENCHMARK() payloads never executed
    database_unchanged(victims)


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_payload_is_stored_as_plain_text(api, victims, payload):
    """Registering with a payload as the name stores exactly those characters, nothing more."""
    r = api.post("/api/auth/register", json={"fullName": f"N {payload}"[:150], "email": "inj@example.test",
                                             "mobileNumber": "7100000099", "password": "Valid-Pass-1"})
    assert r.status_code == 200, r.json()
    victims.expire_all()
    assert victims.scalar(select(User.FullName).where(User.Email == "inj@example.test")) == f"N {payload}"[:150].strip()
    assert victims.scalar(select(func.count()).select_from(User)) == 3


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_orm_lookup_with_payload_matches_nothing(victims, payload):
    assert victims.scalars(select(User).where(User.Email == payload)).all() == []
    assert victims.scalars(select(User).where(User.FullName.contains(payload))).all() == []
    database_unchanged(victims)


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_raw_driver_placeholders_are_safe_too(victims, payload):
    """The same guarantee with a raw PyMySQL cursor (the equivalent of mysqli prepared statements)."""
    raw = victims.connection().connection.dbapi_connection
    with raw.cursor() as cur:
        cur.execute("SELECT Id FROM Users WHERE Email = %s", (payload,))
        assert cur.fetchall() == ()
    database_unchanged(victims)


def test_values_never_appear_in_the_sql_text():
    stmt = select(User).where(User.Email == "' OR '1'='1")
    compiled = stmt.compile(dialect=mysql.dialect())
    assert "OR '1'='1" not in str(compiled)
    assert "`Users`.`Email` = %s" in str(compiled)      # a placeholder; the value travels separately
    assert compiled.params == {"Email_1": "' OR '1'='1"}


def test_string_formatting_would_have_been_vulnerable(victims):
    """Why the rule exists: the same payload glued into SQL text returns every user."""
    payload = "' OR '1'='1"
    unsafe = victims.execute(text(f"SELECT COUNT(*) FROM Users WHERE Email = '{payload}'")).scalar()  # noqa: S608 (deliberate demo)
    safe = victims.execute(text("SELECT COUNT(*) FROM Users WHERE Email = :e"), {"e": payload}).scalar()
    assert (unsafe, safe) == (2, 0)


def test_passwords_are_hashed_never_stored_in_plain_text(api, db):
    api.post("/api/auth/register", json={"fullName": "Hash Check", "email": "hash@example.test",
                                         "mobileNumber": "7100000050", "password": "Plain-Text-Secret-1"})
    stored = db.scalar(select(User.PasswordHash).where(User.Email == "hash@example.test"))
    assert stored.startswith("$argon2id$")
    assert "Plain-Text-Secret-1" not in stored


def test_login_error_does_not_reveal_whether_the_account_exists(api, victims):
    known = api.post("/api/auth/login", json={"email": "victim1@example.test", "password": "wrong-password"})
    unknown = api.post("/api/auth/login", json={"email": "nobody@example.test", "password": "wrong-password"})
    assert known.status_code == unknown.status_code == 401
    assert known.json()["message"] == unknown.json()["message"]
