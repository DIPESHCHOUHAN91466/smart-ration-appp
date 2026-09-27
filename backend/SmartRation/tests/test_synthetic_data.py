"""The central synthetic-data generator (app/synthetic): determinism, safety, validation, insertion."""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

import app.db.models  # noqa: F401
from app.core.security import utc_now
from app.db.database import Base
from app.db.models import (
    AadhaarVerification,
    Beneficiary,
    Family,
    FamilyMember,
    Inventory,
    InventoryMovement,
    RationCollection,
    RationCollectionItem,
    RationShop,
    SchemeEntitlementItem,
    TimeSlot,
    Token,
    TokenItem,
    User,
)
from app.synthetic import SOURCE, SyntheticDataError, book, collect, generate, insert, is_synthetic_email, is_synthetic_mobile, validate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def test_same_seed_same_data_and_different_seed_different_data():
    assert generate(200, seed=2026) == generate(200, seed=2026)
    assert generate(200, seed=2026) != generate(200, seed=7)
    assert generate(50, seed=2026) == generate(200, seed=2026)[:50]   # growing a batch keeps the first records


@pytest.mark.parametrize("count", [1, 10, 100, 1000, 10000])
def test_every_size_is_valid_and_unique(count):
    people = generate(count)
    validate(people)
    for attr in ("email", "mobile", "ration_card", "beneficiary_code", "aadhaar_reference", "passbook_number"):
        assert len({getattr(p, attr) for p in people}) == count


def test_identifiers_are_clearly_synthetic():
    p = generate(1, seed=2026)[0]
    assert p.email == "user0001.s2026@example.com"
    assert p.mobile == "9047000001"                  # block 2026 % 99 + 1 = 47
    assert p.ration_card == "SYN-RC-2026-000001"
    assert p.aadhaar_masked.startswith("XXXX-XXXX-") and len(p.aadhaar_last4) == 4
    assert not any(ch.isdigit() for ch in p.aadhaar_masked[:9])     # no full Aadhaar anywhere
    assert is_synthetic_email(p.email) and is_synthetic_mobile(p.mobile)


def test_no_seed_uses_the_demo_mobile_block():
    assert all(generate(1, seed=s)[0].mobile[2:4] != "00" for s in range(0, 400))


def test_batches_include_devanagari_names_and_families():
    people = generate(300)
    assert any(any("ऀ" <= ch <= "ॿ" for ch in p.full_name) for p in people)
    assert {len(p.members) for p in people} == {1, 2, 3, 4, 5, 6}
    assert all(p.members[0].full_name == p.full_name for p in people)


@pytest.mark.parametrize("change, message", [
    ({"email": "someone@gmail.com"}, "reserved test domain"),
    ({"mobile": "9876543210"}, "synthetic"),
    ({"mobile": "9000000001"}, "synthetic"),                          # the demo accounts' block
    ({"aadhaar_masked": "1234-5678-9012"}, "masked"),
    ({"ration_card": "MH-12-345678"}, "SYN- code"),
    ({"full_name": "A"}, "2-150"),
])
def test_validation_rejects_unsafe_or_invalid_records(change, message):
    people = generate(3)
    people[1] = dataclasses.replace(people[1], **change)
    with pytest.raises(SyntheticDataError, match=message):
        validate(people)


def test_validation_rejects_duplicates():
    people = generate(3)
    people[2] = dataclasses.replace(people[2], email=people[0].email.upper())
    with pytest.raises(SyntheticDataError, match="duplicate email"):
        validate(people)


def test_generate_refuses_bad_counts():
    for bad in (0, -1, 1_000_000):
        with pytest.raises(SyntheticDataError):
            generate(bad)


@pytest.fixture
def sqlite_db(tmp_path, monkeypatch):
    import seed_database

    # Reference data only: without this, a machine (or CI) that sets SEED_DEMO_PASSWORD would also get
    # the 3 demo accounts, and every "exactly N users" assertion below would be off by 3.
    for name in ("SEED_DEMO_PASSWORD", "SEED_ADMIN_EMAIL", "SEED_ADMIN_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    eng = create_engine(f"sqlite:///{tmp_path / 'synthetic_test'}")  # SQLite's "database name" is the path: ends in _test
    Base.metadata.create_all(eng)
    with Session(eng) as db, db.begin():
        seed_database.seed(db)
    yield eng
    eng.dispose()


def test_insert_writes_every_table_with_relationships(sqlite_db):
    people = generate(100)
    with Session(sqlite_db) as db, db.begin():
        counts = insert(db, people, password_hash="not-a-real-hash")
    assert counts["Users"] == 100 and counts["FamilyMembers"] == sum(len(p.members) for p in people)
    with Session(sqlite_db) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 100
        assert db.scalar(select(func.count()).select_from(FamilyMember)) == counts["FamilyMembers"]
        assert db.scalar(select(func.count()).select_from(Beneficiary).where(Beneficiary.DataSource == SOURCE)) == 100
        pairs = db.execute(select(User.Email, Family.FamilyCode, AadhaarVerification.AadhaarMasked)
                           .join(Beneficiary, Beneficiary.UserId == User.Id).join(Family, Family.Id == Beneficiary.FamilyId)
                           .join(AadhaarVerification, AadhaarVerification.BeneficiaryId == Beneficiary.Id)).all()
        expected = {(p.email, p.ration_card, p.aadhaar_masked) for p in people}
        assert set(map(tuple, pairs)) == expected


def test_insert_validates_first_and_writes_nothing_when_invalid(sqlite_db):
    people = generate(5)
    people[4] = dataclasses.replace(people[4], mobile="9876543210")
    with Session(sqlite_db) as db, pytest.raises(SyntheticDataError), db.begin():
        insert(db, people, password_hash="x")
    with Session(sqlite_db) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 0


def _cli(*args, **env):
    full_env = {**os.environ, "JWT_SECRET_KEY": "unit-test-signing-key-0123456789abcdef-0123456789", "PYTHONIOENCODING": "utf-8", **env}
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_test_data.py"), *args], cwd=ROOT, env=full_env,
                          capture_output=True, text=True, encoding="utf-8", timeout=180)


def test_cli_generates_json_without_touching_a_database(tmp_path):
    out = tmp_path / "people.json"
    result = _cli("--users", "25", "--seed", "11", "--json", str(out), DATABASE_URL="sqlite:///does-not-matter.db")
    assert result.returncode == 0, result.stdout + result.stderr
    document = json.loads(out.read_text(encoding="utf-8"))
    assert document["_meta"] == {"isSynthetic": True, "seed": 11, "count": 25}
    assert document["records"][0]["email"] == "user0001.s11@example.com"


def test_cli_insert_refuses_a_non_test_database(tmp_path):
    result = _cli("--users", "5", "--insert", TEST_DATABASE_URL=f"sqlite:///{tmp_path / 'smartration.db'}")
    assert result.returncode != 0 and "does not end in _test" in (result.stdout + result.stderr)


def test_cli_insert_refuses_real_data_mode(tmp_path):
    result = _cli("--users", "5", "--insert", DATA_MODE="real", TEST_DATABASE_URL=f"sqlite:///{tmp_path / 'x_test'}")
    assert result.returncode == 1 and "DATA_MODE" in result.stdout


def test_cli_inserts_into_a_test_database_once_per_seed(sqlite_db):
    url = sqlite_db.url.render_as_string(hide_password=False)
    first = _cli("--users", "30", "--seed", "5", "--insert", TEST_DATABASE_URL=url)
    assert first.returncode == 0, first.stdout + first.stderr
    assert "Users 30" in first.stdout
    again = _cli("--users", "30", "--seed", "5", "--insert", TEST_DATABASE_URL=url)
    assert again.returncode == 1 and "already exist" in again.stdout
    with Session(sqlite_db) as db:
        assert db.scalar(select(func.count()).select_from(User)) == 30          # the failed rerun changed nothing


# ------------------------------------------------------------------ bookings (tokens + time slots)

def test_book_gives_each_citizen_one_upcoming_token_within_capacity(sqlite_db):
    people = generate(100)
    with Session(sqlite_db) as db, db.begin():
        insert(db, people, password_hash="x")
        counts = book(db, people)
    assert counts["Tokens"] == 100 and counts["Unbooked"] == 0
    with Session(sqlite_db) as db:
        tokens = db.scalars(select(Token)).all()
        assert len({t.UserId for t in tokens}) == 100 and len({t.TokenNumber for t in tokens}) == 100
        assert all(t.TokenNumber == f"SR-{t.CreatedAt:%Y}-{t.Id:06d}" and t.Status == 2 and t.QRCodeValue is None for t in tokens)
        slots = {s.Id: s for s in db.scalars(select(TimeSlot)).all()}
        assert all(slots[t.TimeSlotId].RationShopId == t.RationShopId for t in tokens)
        assert all(s.BookedCount <= s.Capacity for s in slots.values())
        assert sum(s.BookedCount for s in slots.values()) == 100
        entitled = db.scalar(select(func.count()).select_from(SchemeEntitlementItem)
                             .where(SchemeEntitlementItem.RationSchemeId == db.scalar(select(Family.RationSchemeId).limit(1))))
        assert counts["TokenItems"] == db.scalar(select(func.count()).select_from(TokenItem)) == 100 * entitled


def test_book_stops_at_capacity_and_reports_the_rest(sqlite_db):
    with Session(sqlite_db) as db, db.begin():
        first_shop = db.scalar(select(RationShop.Id).order_by(RationShop.Id).limit(1))
        db.query(RationShop).filter(RationShop.Id != first_shop).update({"IsActive": False})
        db.query(TimeSlot).update({"BookedCount": TimeSlot.Capacity})
        one = db.scalar(select(TimeSlot.Id).where(TimeSlot.RationShopId == first_shop).order_by(TimeSlot.SlotDate.desc()).limit(1))
        db.query(TimeSlot).filter(TimeSlot.Id == one).update({"BookedCount": TimeSlot.Capacity - 1})
        people = generate(3)
        insert(db, people, password_hash="x")
        counts = book(db, people)
    assert counts == {"Tokens": 1, "TokenItems": counts["TokenItems"], "Unbooked": 2}
    with Session(sqlite_db) as db:
        slot = db.get(TimeSlot, one)
        assert slot.BookedCount == slot.Capacity


def test_book_requires_inserted_citizens(sqlite_db):
    with Session(sqlite_db) as db, pytest.raises(SyntheticDataError, match="insert the citizens"):
        book(db, generate(2))


def test_cli_insert_with_bookings(sqlite_db):
    url = sqlite_db.url.render_as_string(hide_password=False)
    result = _cli("--users", "20", "--seed", "8", "--insert", "--bookings", TEST_DATABASE_URL=url)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Tokens 20" in result.stdout and "Unbooked 0" in result.stdout


# ------------------------------------------------------------------ collections (transactions + stock ledger)

def _stock(db) -> dict:
    return {(i.RationShopId, i.RationType): (i.AvailableQuantity, i.AllocatedQuantity) for i in db.scalars(select(Inventory))}


def test_collect_records_transactions_and_moves_stock_exactly(sqlite_db):
    people = generate(40)
    with Session(sqlite_db) as db, db.begin():
        insert(db, people, password_hash="x")
        before = _stock(db)
        counts = collect(db, people, share=0.5)
    assert counts["NotSelected"] == 20 and counts["Collections"] + counts["NotCollected"] == 20 and counts["Collections"] > 0
    with Session(sqlite_db) as db:
        collections = db.scalars(select(RationCollection)).all()
        assert len(collections) == counts["Collections"]
        assert all(c.CollectionCode == f"COL-SYN-{c.Id:06d}" for c in collections)
        tokens = {t.Id: t for t in db.scalars(select(Token))}
        assert all(tokens[c.TokenId].Status == 3 and tokens[c.TokenId].CollectedAt == c.CollectedAt for c in collections)
        slots = {s.Id: s for s in db.scalars(select(TimeSlot))}
        assert all(slots[tokens[c.TokenId].TimeSlotId].SlotDate.date() < utc_now().date() for c in collections)   # past slots only
        assert all(s.BookedCount <= s.Capacity for s in slots.values())
        # every issued unit is on the ledger and left "available" for "allocated"; nothing went negative
        issued: dict = {}
        for item in db.scalars(select(RationCollectionItem)):
            shop = next(c.RationShopId for c in collections if c.Id == item.RationCollectionId)
            issued[(shop, item.RationType)] = issued.get((shop, item.RationType), 0) + item.Quantity
        after = _stock(db)
        for key, qty in issued.items():
            assert after[key][0] == before[key][0] - qty and after[key][1] == before[key][1] + qty and after[key][0] >= 0
        movements = db.scalars(select(InventoryMovement)).all()
        assert len(movements) == db.scalar(select(func.count()).select_from(RationCollectionItem))
        assert all(m.MovementType == 2 and m.BalanceAfter >= 0 for m in movements)


def test_collect_never_issues_more_than_the_shop_has(sqlite_db):
    people = generate(30)
    with Session(sqlite_db) as db, db.begin():
        insert(db, people, password_hash="x")
        db.query(Inventory).update({"AvailableQuantity": 0})
        counts = collect(db, people, share=1.0)
    assert counts == {"Collections": 0, "NotCollected": 30, "NotSelected": 0}
    with Session(sqlite_db) as db:
        assert db.scalar(select(func.count()).select_from(RationCollection)) == 0
        assert db.scalar(select(func.count()).select_from(InventoryMovement)) == 0


def test_collect_rejects_a_bad_share(sqlite_db):
    with Session(sqlite_db) as db, pytest.raises(SyntheticDataError, match="share"):
        collect(db, generate(2), share=1.5)


def test_cli_insert_with_bookings_and_collections(sqlite_db):
    url = sqlite_db.url.render_as_string(hide_password=False)
    result = _cli("--users", "20", "--seed", "9", "--insert", "--bookings", "--collections", "0.5", TEST_DATABASE_URL=url)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Tokens 20" in result.stdout and "Collections " in result.stdout and "NotSelected 10" in result.stdout
