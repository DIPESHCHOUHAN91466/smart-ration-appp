"""Security N8: the running API works with an account that may only read and write rows, and that account cannot
change the schema. Needs TEST_MYSQL_ROOT_URL (an account that may create users; CI sets it), else skipped."""

from __future__ import annotations

import os
import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.config.settings import Settings
from app.main import create_app
from mysql_suite.support import KEY, QR_TEST_SECRET

ROOT_URL = os.environ.get("TEST_MYSQL_ROOT_URL", "")
pytestmark = pytest.mark.skipif(not ROOT_URL, reason="TEST_MYSQL_ROOT_URL not set (needs an account that may create users)")
USER = "sr_rows_only_test"


@pytest.fixture
def rows_only_url(engine, test_url):
    """A throwaway account with SELECT/INSERT/UPDATE/DELETE on the test database only."""
    password = secrets.token_urlsafe(18)
    database = make_url(test_url).database
    root = create_engine(ROOT_URL)
    with root.begin() as conn:
        conn.execute(text(f"DROP USER IF EXISTS '{USER}'@'%'"))
        conn.execute(text(f"CREATE USER '{USER}'@'%' IDENTIFIED BY :pw"), {"pw": password})
        conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{database}`.* TO '{USER}'@'%'"))
    try:
        yield make_url(test_url).set(username=USER, password=password).render_as_string(hide_password=False)
    finally:
        with root.begin() as conn:
            conn.execute(text(f"DROP USER IF EXISTS '{USER}'@'%'"))
        root.dispose()


def test_the_api_runs_with_a_rows_only_account(rows_only_url, db):
    settings = Settings(_env_file=None, database_url=rows_only_url, legacy_api_url="", jwt_secret_key=KEY,
                        qr_secret=QR_TEST_SECRET, ai_service_url="", auth_rate_limit_per_minute=100_000, log_level="WARNING")
    with TestClient(create_app(settings), raise_server_exceptions=False) as api:
        assert api.get("/health/db").json()["status"] == "healthy"
        r = api.post("/api/auth/register", json={"fullName": "Least Privilege", "email": "rows-only@example.test",
                                                 "mobileNumber": "7300000099", "password": "Kite-River-Lamp-42"})
        assert r.status_code == 200, r.text
        token = r.json()["data"]["accessToken"]
        assert api.get("/api/users/profile", headers={"Authorization": f"Bearer {token}"}).status_code == 200


@pytest.mark.parametrize("statement", ["DROP TABLE Users", "CREATE TABLE sr_probe (id INT)", "ALTER TABLE Users ADD COLUMN x INT",
                                       "TRUNCATE TABLE AuditLogs"])
def test_the_rows_only_account_cannot_change_the_schema(rows_only_url, statement):
    eng = create_engine(rows_only_url)
    try:
        with pytest.raises((OperationalError, ProgrammingError)) as refused, eng.begin() as conn:
            conn.execute(text(statement))
        assert "denied" in str(refused.value).lower()
    finally:
        eng.dispose()
