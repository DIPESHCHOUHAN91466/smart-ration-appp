"""Error handling: failures are fast, reported cleanly, logged without secrets, and never leave
half-written data behind. The app recovers once the problem goes away."""

from __future__ import annotations

import io
import logging
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.config import Settings
from app.db import database
from app.db.models import User
from app.main import create_app

from .conftest import KEY, new_session


@pytest.fixture
def restore_engine(test_url):
    """Tests that point the app at a broken database put the real test DB back afterwards."""
    yield
    database.configure_database(test_url)


def test_wrong_password_fails_fast_without_leaking_it(test_url):
    bad = make_url(test_url).set(password="definitely-wrong-pw")
    eng = create_engine(bad, connect_args={"connect_timeout": 5})
    start = time.perf_counter()
    with pytest.raises(OperationalError) as err:
        eng.connect()
    assert err.value.orig.args[0] == 1045                      # access denied
    assert "definitely-wrong-pw" not in str(err.value)
    assert time.perf_counter() - start < 6


def test_unreachable_server_times_out_quickly(test_url):
    eng = create_engine(make_url(test_url).set(host="127.0.0.1", port=1), connect_args={"connect_timeout": 3})
    start = time.perf_counter()
    with pytest.raises(OperationalError):
        eng.connect()
    assert time.perf_counter() - start < 6                     # no hanging requests


def test_health_reports_database_down_without_details(test_url, restore_engine):
    bad = make_url(test_url).set(password="definitely-wrong-pw").render_as_string(hide_password=False)
    app = create_app(Settings(_env_file=None, database_url=bad, legacy_api_url="", jwt_secret_key=KEY))
    with TestClient(app, raise_server_exceptions=False) as client:
        health, ready = client.get("/health"), client.get("/ready")
        login = client.post("/api/auth/login", json={"email": "a@example.test", "password": "whatever-123"})
    assert health.status_code == 503 and health.json()["database"] == "unhealthy"
    assert ready.status_code == 503 and ready.json()["checks"]["database"] == "failing"
    assert login.status_code == 500 and login.json()["errorCode"] == "INTERNAL_ERROR"
    for body in (health.text, ready.text, login.text):
        assert "definitely-wrong-pw" not in body and "mysql" not in body.lower() and "1045" not in body


def test_query_error_returns_clean_500_and_rolls_back(api, db, test_url):
    """A real database error mid-request (table missing) → generic 500, no SQL in the response,
    nothing half-written, and the API works again once the table is back."""
    body = {"fullName": "Err Case", "email": "err@example.test", "mobileNumber": "7400000001", "password": "Valid-Pass-1"}
    with database.get_engine().begin() as conn:
        conn.execute(text("RENAME TABLE RefreshTokens TO RefreshTokens_hidden"))
    try:
        r = api.post("/api/auth/register", json=body)
    finally:
        with database.get_engine().begin() as conn:
            conn.execute(text("RENAME TABLE RefreshTokens_hidden TO RefreshTokens"))
    assert r.status_code == 500
    assert r.json() == {"success": False, "message": "An unexpected error occurred. Please try again later.",
                        "data": None, "errors": None, "errorCode": "INTERNAL_ERROR"}
    assert "refreshtokens" not in r.text.lower() and "insert" not in r.text.lower()
    assert r.headers.get("x-request-id")                         # the id to find the full error in the logs
    assert db.scalar(select(func.count()).select_from(User)) == 0  # the user insert was rolled back too

    assert api.post("/api/auth/register", json=body).status_code == 200  # recovered


def test_registration_aborts_cleanly_when_setup_is_missing(api, db):
    with database.get_engine().begin() as conn:
        conn.execute(text("UPDATE RationShops SET IsActive = 0"))
    r = api.post("/api/auth/register", json={"fullName": "No Shop", "email": "noshop@example.test",
                                             "mobileNumber": "7400000002", "password": "Valid-Pass-1"})
    assert r.status_code == 400
    assert r.json()["message"] == "No active ration shop is configured to assign this beneficiary to."
    assert db.scalar(select(func.count()).select_from(User)) == 0  # the flushed user did not survive


def test_transaction_is_all_or_nothing(db, make_user):
    db.add(make_user("tx1@example.test", "7400000010"))
    db.add(make_user("tx1@example.test", "7400000011"))           # duplicate in the same transaction
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_killed_connection_is_detected_and_replaced(engine):
    """Simulates MySQL restarting / a network drop: the in-flight transaction fails with a clear
    error, and the pool (pre-ping) hands out a working connection next time."""
    victim = new_session()
    victim_id = victim.execute(text("SELECT CONNECTION_ID()")).scalar()
    with engine.connect() as killer:
        killer.execute(text(f"KILL {int(victim_id)}"))
    with pytest.raises(OperationalError) as err:
        victim.execute(text("SELECT 1"))
    assert err.value.orig.args[0] in (2006, 2013, 1927, 4031)           # server gone / lost connection
    victim.rollback()
    victim.close()

    with new_session() as fresh:
        assert fresh.execute(text("SELECT 1")).scalar() == 1
        assert fresh.execute(text("SELECT CONNECTION_ID()")).scalar() != victim_id


def test_lock_wait_times_out_instead_of_hanging(db):
    slot_id = db.scalar(text("SELECT MIN(Id) FROM TimeSlots"))
    db.rollback()
    with new_session() as holder, new_session() as waiter:
        holder.execute(text("SELECT Id FROM TimeSlots WHERE Id = :i FOR UPDATE"), {"i": slot_id})
        waiter.execute(text("SET SESSION innodb_lock_wait_timeout = 1"))
        start = time.perf_counter()
        with pytest.raises(OperationalError) as err:
            waiter.execute(text("SELECT Id FROM TimeSlots WHERE Id = :i FOR UPDATE"), {"i": slot_id})
        assert err.value.orig.args[0] == 1205                    # lock wait timeout exceeded
        assert time.perf_counter() - start < 5
        waiter.rollback()
        waiter.execute(text("SET SESSION innodb_lock_wait_timeout = DEFAULT"))
        holder.rollback()


def test_logs_never_contain_passwords_or_tokens(api, db):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.getLogger().handlers[0].formatter)  # the app's own JSON formatter
    logger = logging.getLogger("smartration")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        reg = api.post("/api/auth/register", json={"fullName": "Log Check", "email": "log@example.test",
                                                   "mobileNumber": "7400000020", "password": "Log-Secret-Pass-1"})
        api.post("/api/auth/login?password=Query-Secret-1", json={"email": "log@example.test", "password": "Wrong-Secret-Pass-2"})
        api.post("/api/auth/login", json={"email": "log@example.test", "password": "Log-Secret-Pass-1"})
    finally:
        logger.removeHandler(handler)
        logger.setLevel(logging.NOTSET)
    logs = stream.getvalue()
    assert "user registered" in logs                               # logging works...
    tokens = reg.json()["data"]
    for secret in ("Log-Secret-Pass-1", "Wrong-Secret-Pass-2", "Query-Secret-1", tokens["accessToken"], tokens["refreshToken"], KEY):
        assert secret not in logs                                  # ...but never with secrets
