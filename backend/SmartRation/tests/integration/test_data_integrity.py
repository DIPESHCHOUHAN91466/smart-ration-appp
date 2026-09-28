"""database/queries/*.sql run by app.database.integrity: a clean database passes, each broken rule is found,
and nothing a check does can change data."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import time, timedelta

import pytest
from py_testkit import BACKEND_ROOT
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (register tables)
from app.database.base import Base
from app.database.integrity import QUERIES_DIR, InvalidCheck, load_checks, parse_check, run_checks
from app.models import (
    AadhaarVerification,
    Beneficiary,
    Family,
    Inventory,
    RationCollection,
    RationCollectionItem,
    RationScheme,
    RationShop,
    TimeSlot,
    Token,
    User,
)
from app.utils.time import utc_now


@pytest.fixture
def engine(tmp_path):
    eng = create_engine(f"sqlite:///{(tmp_path / 'integrity.db').as_posix()}")
    Base.metadata.create_all(eng)
    now = utc_now()
    with Session(eng) as db:
        db.add_all([
            RationShop(Id=1, ShopName="Shop", ShopCode="S-1", Address="a", District="d", State="s", Latitude=0, Longitude=0, IsActive=True, CreatedAt=now),
            RationScheme(Id=1, SchemeCode="DEMO-NFSA", Name="NFSA", Description="", IsActive=True),
            User(Id=1, FullName="A", Email="a@example.com", MobileNumber="9000000001", PasswordHash="x", Role=1, IsActive=True, CreatedAt=now),
            User(Id=2, FullName="Owner", Email="owner@example.com", MobileNumber="9000000051", PasswordHash="x", Role=2, IsActive=True, CreatedAt=now, RationShopId=1),
            TimeSlot(Id=1, RationShopId=1, SlotDate=now - timedelta(days=1), StartTime=time(10), EndTime=time(10, 5), Capacity=2, BookedCount=1),
            Token(Id=1, TokenNumber="T-1", UserId=1, RationShopId=1, TimeSlotId=1, Status=3, CreatedAt=now, CollectedAt=now),
            Token(Id=2, TokenNumber="T-2", UserId=1, RationShopId=1, TimeSlotId=1, Status=4, CreatedAt=now),  # cancelled: holds no place
            Inventory(Id=1, RationShopId=1, RationType=1, AvailableQuantity=10, AllocatedQuantity=5, MinimumStockLevel=1, UpdatedAt=now),
            Family(Id=1, FamilyCode="FAM-1", RationShopId=1, RationSchemeId=1, DataSource="SYNTHETIC_DEMO", CreatedAt=now),
        ])
        db.flush()
        db.add(Beneficiary(Id=1, BeneficiaryCode="BEN-1", Address="a", UserId=1, FamilyId=1, IsActive=True, IsBlocked=False, DataSource="SYNTHETIC_DEMO",
                           CreatedAt=now, Gender=3, DateOfBirth=now, Village="", District="", State="", Pincode=""))
        db.flush()
        db.add(AadhaarVerification(Id=1, BeneficiaryId=1, AadhaarReferenceId="AAD-1", AadhaarMasked="XXXX-XXXX-1234", Status=2,
                                   VerificationDate=now, VerificationSource="SYNTHETIC_DEMO", VerificationMode="PRE_VERIFIED"))
        db.add(RationCollection(Id=1, CollectionCode="COL-1", TokenId=1, BeneficiaryId=1, RationShopId=1, OperatorUserId=2, VerificationMethod="QR", CollectedAt=now))
        db.flush()
        db.add(RationCollectionItem(Id=1, RationCollectionId=1, RationType=1, Quantity=5))
        db.commit()
    yield eng
    eng.dispose()


def failures(engine) -> dict[str, list[str]]:
    return {r.check.name: r.sample_ids for r in run_checks(engine, load_checks()) if r.failed}


def test_the_query_files_are_valid_and_uniquely_named():
    checks = load_checks()
    assert len(checks) >= 8 and all(c.why for c in checks)
    assert {c.severity for c in checks} <= {"error", "warning"}


def test_a_consistent_database_passes_every_check(engine):
    assert failures(engine) == {}


def test_each_broken_rule_is_reported_by_id(engine):
    with Session(engine) as db:
        db.get(TimeSlot, 1).BookedCount = 3                    # over capacity (and drifted)
        db.get(Inventory, 1).AvailableQuantity = -1            # negative stock
        db.get(Token, 1).Status = 2                            # collected token still open
        db.get(AadhaarVerification, 1).AadhaarMasked = "999900001234"  # unmasked
        db.get(User, 2).RationShopId = None                    # shop owner without shop
        db.add(User(Id=3, FullName="Dup", Email="A@EXAMPLE.COM", MobileNumber="9000000003", PasswordHash="x", Role=1, IsActive=True, CreatedAt=utc_now()))
        db.add(RationCollection(Id=2, CollectionCode="COL-2", TokenId=2, BeneficiaryId=1, RationShopId=1, OperatorUserId=2, VerificationMethod="QR", CollectedAt=utc_now()))
        db.commit()
    found = failures(engine)
    assert found["overbooked_time_slots"] == ["1"]
    assert found["negative_inventory"] == ["1"]
    assert found["collections_with_open_tokens"] == ["1", "2"]
    assert found["collections_without_items"] == ["2"]
    assert found["unmasked_aadhaar"] == ["1"]
    assert found["duplicate_emails_ignoring_case"] == ["1"]
    assert found["shop_owners_without_shop"] == ["2"]
    assert found["slot_count_drift"] == ["1"]


def test_results_never_contain_personal_values(engine):
    with Session(engine) as db:
        db.get(AadhaarVerification, 1).AadhaarMasked = "999900001234"
        db.commit()
    for result in run_checks(engine, load_checks()):
        assert all("9999" not in value and "@" not in value for value in result.sample_ids)


def test_non_select_statements_are_refused(tmp_path):
    for body in ("DELETE FROM Users", "UPDATE Users SET Role = 4", "SELECT 1; DROP TABLE Users", "DROP TABLE Users"):
        f = tmp_path / "bad.sql"
        f.write_text(f"-- check: bad\n-- severity: error\n{body}\n", encoding="utf-8")
        with pytest.raises(InvalidCheck):
            parse_check(f)


def test_a_check_cannot_change_data_even_if_it_tried(engine, tmp_path):
    # SQLite allows a CTE in front of a SELECT only; the transaction is rolled back regardless.
    f = tmp_path / "count.sql"
    f.write_text("-- check: count_users\n-- severity: warning\nWITH u AS (SELECT Id FROM Users) SELECT Id AS id FROM u\n", encoding="utf-8")
    run_checks(engine, [parse_check(f)])
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 2


def test_the_command_line_tool_reports_and_sets_the_exit_code(engine, tmp_path):
    env = {**os.environ, "DATABASE_URL": engine.url.render_as_string(hide_password=False), "INTEGRITY_QUERIES_DIR": str(QUERIES_DIR)}
    ok = subprocess.run([sys.executable, "scripts/check_data_integrity.py"], cwd=BACKEND_ROOT, env=env, capture_output=True, text=True)
    assert ok.returncode == 0 and "Integrity OK" in ok.stdout and "[PASS] unmasked_aadhaar: 0" in ok.stdout
    with Session(engine) as db:
        db.get(Inventory, 1).AvailableQuantity = -5
        db.commit()
    bad = subprocess.run([sys.executable, "scripts/check_data_integrity.py"], cwd=BACKEND_ROOT, env=env, capture_output=True, text=True)
    assert bad.returncode == 1 and "[FAIL] negative_inventory: 1  ids: 1" in bad.stdout
