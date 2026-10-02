"""The database scripts, end to end, against throwaway SQLite files."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest
from py_testkit import BACKEND_ROOT
from sqlalchemy import create_engine, func, select, text

import app.database.models  # noqa: F401
from app.database.base import Base
from app.database.models import RationItem, User

ROOT = BACKEND_ROOT
RESET_FLAGS = {"RESET_DATABASE": "true", "CONFIRM_RESET": "SMART_RATION_RESET"}


def run(script: str, db_url: str, *args: str, **env: str) -> subprocess.CompletedProcess:
    full_env = {k: v for k, v in os.environ.items() if k not in {"RESET_DATABASE", "CONFIRM_RESET", "APP_ENV", "ENVIRONMENT"}}
    full_env.update(DATABASE_URL=db_url, JWT_SECRET_KEY="unit-test-signing-key-0123456789abcdef-0123456789",
                    SEED_DEMO_PASSWORD="unit-demo-password", PYTHONIOENCODING="utf-8", **env)
    return subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT, env=full_env,
                          capture_output=True, text=True, encoding="utf-8", timeout=180)


@pytest.fixture
def db_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'scripts.db').as_posix()}"


def count(url: str, model) -> int:
    eng = create_engine(url)
    with eng.connect() as conn:
        n = conn.scalar(select(func.count()).select_from(model))
    eng.dispose()
    return n


def test_setup_creates_seeds_and_verifies_empty_database(db_url):
    result = run("setup_database.py", db_url, "--seed")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Empty database" in result.stdout
    assert "DATABASE VERIFICATION PASSED" in result.stdout
    assert count(db_url, RationItem) == 6 and count(db_url, User) == 3


def test_first_boot_demo_citizen_can_sign_in_see_their_card_and_book(db_url, tmp_path):
    """What a fresh cloud deployment does (RUN_DB_SETUP + RUN_DB_SEED with SEED_DEMO_PASSWORD), then the demo
    citizen's first journey through the real API: sign in, ration card, book a slot, get the signed QR."""
    from datetime import date, timedelta

    from fastapi.testclient import TestClient
    from py_testkit import make_settings

    from app.main import create_app

    assert run("setup_database.py", db_url, "--seed").returncode == 0
    client = TestClient(create_app(make_settings(tmp_path, database_url=db_url, legacy_api_url="", max_request_bytes=65536)))

    r = client.post("/api/auth/login", json={"email": "rural@example.com", "password": "unit-demo-password"})
    assert r.status_code == 200, r.text
    citizen = {"Authorization": f"Bearer {r.json()['data']['accessToken']}"}
    me = client.get("/api/beneficiaries/me", headers=citizen)
    assert me.status_code == 200, me.text
    shop = me.json()["data"]["rationShop"]
    assert shop["shopName"].startswith("Satnavari"), shop   # the same shop as the demo shop owner

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    slots = client.get(f"/api/slots?shopId={shop['id']}&date={tomorrow}", headers=citizen).json()["data"]
    assert slots, "the seed creates bookable slots"
    booked = client.post("/api/ration/bookings", headers=citizen, json={
        "rationShopId": shop["id"], "timeSlotId": slots[0]["id"], "items": [{"rationType": "Rice", "quantity": 1}]})
    assert booked.status_code == 200, booked.text
    qr = client.get(f"/api/qr/payload/{booked.json()['data']['id']}", headers=citizen)
    assert qr.status_code == 200 and qr.json()["data"]


def test_setup_and_seed_are_idempotent(db_url):
    assert run("setup_database.py", db_url, "--seed").returncode == 0
    again = run("setup_database.py", db_url, "--seed")
    assert again.returncode == 0, again.stdout + again.stderr
    assert "Nothing to seed" in again.stdout
    assert count(db_url, RationItem) == 6 and count(db_url, User) == 3


def test_setup_adopts_an_existing_ef_database_without_touching_data(db_url):
    eng = create_engine(db_url)
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE __EFMigrationsHistory (MigrationId varchar(150) PRIMARY KEY, ProductVersion varchar(32))"))
        conn.execute(text("INSERT INTO RationItems (RationType, Name, VernacularName, Unit, StandardQuotaPerBooking, IsActive) "
                          "VALUES (1, 'Existing rice', 'x', 'kg', 5, 1)"))
    eng.dispose()

    result = run("setup_database.py", db_url, "--seed")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "stamp 0001_initial" in result.stdout
    assert count(db_url, RationItem) == 1  # existing data kept; the table wasn't reseeded


def test_setup_refuses_a_partial_schema(db_url):
    eng = create_engine(db_url)
    Base.metadata.tables["RationItems"].create(eng)
    eng.dispose()
    result = run("setup_database.py", db_url)
    assert result.returncode == 1
    assert "Refusing" in result.stdout


def test_verify_fails_on_drift(db_url):
    assert run("setup_database.py", db_url, "--seed").returncode == 0
    eng = create_engine(db_url)
    with eng.begin() as conn:
        conn.execute(text("DROP INDEX IX_Users_Email"))
    eng.dispose()
    result = run("verify_database.py", db_url)
    assert result.returncode == 1
    assert "DATABASE VERIFICATION FAILED" in result.stdout and "IX_Users_Email" in result.stdout


@pytest.mark.parametrize("env,args", [
    ({}, ["--yes-i-typed-it", "scripts.db"]),                                     # no confirmation flags
    ({"RESET_DATABASE": "true"}, ["--yes-i-typed-it", "scripts.db"]),              # only one flag
    ({**RESET_FLAGS, "ENVIRONMENT": "production"}, ["--yes-i-typed-it", "x"]),    # production
    (RESET_FLAGS, ["--yes-i-typed-it", "wrong-name"]),                            # name not typed
])
def test_reset_refuses_without_every_confirmation(db_url, env, args):
    assert run("setup_database.py", db_url, "--seed").returncode == 0
    result = run("reset_database.py", db_url, *args, **env)
    assert result.returncode == 1
    assert count(db_url, User) == 3  # nothing dropped


def test_reset_with_every_confirmation_recreates_and_reseeds(db_url, tmp_path):
    assert run("setup_database.py", db_url, "--seed").returncode == 0
    name = str(tmp_path / "scripts.db").replace("\\", "/")
    result = run("reset_database.py", db_url, "--yes-i-typed-it", name, **RESET_FLAGS)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DATABASE VERIFICATION PASSED" in result.stdout


def test_verify_fails_without_reference_data(db_url):
    result = run("setup_database.py", db_url)  # schema only, no --seed
    assert result.returncode == 1
    assert "No ration items found" in result.stdout


def test_migration_downgrade_is_guarded(db_url):
    assert run("setup_database.py", db_url, "--seed").returncode == 0
    env = {k: v for k, v in os.environ.items() if k not in RESET_FLAGS}
    env.update(DATABASE_URL=db_url, JWT_SECRET_KEY="unit-test-signing-key-0123456789abcdef-0123456789")
    result = subprocess.run([sys.executable, "-m", "alembic", "downgrade", "base"], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode != 0 and "Refusing to drop" in result.stderr
    assert count(db_url, RationItem) == 6  # nothing dropped


def test_every_path_the_scripts_depend_on_exists():
    """Regression: after the folder restructure, reset_database.py still pointed at database/mysql/backup.ps1."""
    code = ("import sys; sys.path.insert(0, 'scripts'); "
            "import reset_database, seed_database, export_openapi, export_schema_sql; "
            "from app.database.integrity import QUERIES_DIR; from app.database.migrations import MIGRATIONS_DIR; "
            "paths = [reset_database.BACKUP_SCRIPT, seed_database.DATA_DIR, export_openapi.OUT, "
            "export_schema_sql.OUTPUT.parent, export_schema_sql.MIGRATIONS_OUTPUT, QUERIES_DIR, MIGRATIONS_DIR]; "
            "missing = [str(p) for p in paths if not p.exists()]; print(missing); sys.exit(1 if missing else 0)")
    env = {k: v for k, v in os.environ.items() if k not in ("SYNTHETIC_DATA_DIR", "INTEGRITY_QUERIES_DIR")}
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
