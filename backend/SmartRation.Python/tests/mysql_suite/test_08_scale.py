"""Scale: 1000 synthetic citizens through CREATE / READ / UPDATE / DELETE, and concurrency at 10, 25,
50 and 100 simultaneous operations.

Data comes from the central generator (app/synthetic, seed 2026), so every run uses the same
records. Concurrency tests reproduce the C# API's own pattern: optimistic concurrency on
TimeSlots.BookedCount and Inventory.AvailableQuantity ([ConcurrencyCheck] -> UPDATE ... WHERE
column = <value read>; 0 rows = someone else won). Losers retry, as a user would after a 409.
Timings print in the "MySQL performance" section; the assertions only pin down correctness and
generous upper bounds, never exact speeds.
"""

from __future__ import annotations

import time
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, delete, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.core.security import utc_now
from app.db.models import (
    AadhaarVerification,
    Beneficiary,
    Family,
    FamilyMember,
    Inventory,
    MobileVerification,
    PassbookVerification,
    RationShop,
    TimeSlot,
    Token,
    User,
)
from app.synthetic import SOURCE, generate, insert
from mysql_suite.support import new_session, stats
from mysql_suite.test_05_concurrency import run_parallel

LEVELS = [10, 25, 50, 100]
CONFIRMED = 2  # C# TokenStatus.Confirmed (Models/Token.cs)
PERSON_TABLES = [User, Family, FamilyMember, Beneficiary, MobileVerification, AadhaarVerification, PassbookVerification]


def _is_devanagari(value: str) -> bool:
    return any("ऀ" <= ch <= "ॿ" for ch in value)


def _count(db: Session, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


# ------------------------------------------------------------------ 1000 records, CRUD

def test_1000_synthetic_citizens_create_read_update_delete(db, password_hash, record):
    people = generate(1000, seed=2026)
    expected_members = sum(len(p.members) for p in people)
    shops_before = _count(db, RationShop)
    started = utc_now().replace(microsecond=0)

    # CREATE: seven tables, one transaction
    t0 = time.perf_counter()
    counts = insert(db, people, password_hash)
    db.commit()
    record("CREATE 1000 citizens (7 tables, 1 transaction)", time.perf_counter() - t0, f"{sum(counts.values())} rows")
    assert {m.__tablename__: _count(db, m) for m in PERSON_TABLES} == {
        "Users": 1000, "Families": 1000, "FamilyMembers": expected_members, "Beneficiaries": 1000,
        "MobileVerifications": 1000, "AadhaarVerifications": 1000, "PassbookVerifications": 1000}

    # READ: every row back exactly as generated (encoding, quoting, no truncation)
    by_email = {p.email: p for p in people}
    samples = []
    ids = list(db.scalars(select(User.Id).order_by(User.Id)))
    for user_id in ids:
        t = time.perf_counter()
        row = db.execute(select(User.Email, User.FullName, User.MobileNumber).where(User.Id == user_id)).one()
        samples.append(time.perf_counter() - t)
        p = by_email[row.Email]
        assert (row.FullName, row.MobileNumber) == (p.full_name, p.mobile)
    record("READ 1000 users by primary key, one query each", sum(samples), stats(samples))
    t = time.perf_counter()
    everyone = db.execute(select(User.Email, User.FullName)).all()
    record("READ 1000 users, one query", time.perf_counter() - t, "")
    assert len(everyone) == 1000
    stored_devanagari = sum(_is_devanagari(name) for _, name in everyone)
    assert stored_devanagari == sum(_is_devanagari(p.full_name) for p in people) > 0

    # Relationships: every user -> beneficiary -> family -> Aadhaar row, and the values line up
    joined = db.execute(select(User.Email, Family.FamilyCode, AadhaarVerification.AadhaarMasked, Beneficiary.DataSource)
                        .join(Beneficiary, Beneficiary.UserId == User.Id).join(Family, Family.Id == Beneficiary.FamilyId)
                        .join(AadhaarVerification, AadhaarVerification.BeneficiaryId == Beneficiary.Id)).all()
    assert {(e, f, a) for e, f, a, _ in joined} == {(p.email, p.ration_card, p.aadhaar_masked) for p in people}
    assert {s for *_, s in joined} == {SOURCE}
    heads = db.scalar(select(func.count()).select_from(FamilyMember).where(FamilyMember.Relationship == 1))
    assert heads == 1000

    # Timestamps set, in this run's window
    oldest, newest = db.execute(select(func.min(User.CreatedAt), func.max(User.CreatedAt))).one()
    assert started <= oldest <= newest <= utc_now()

    # UPDATE: 1000 single-row transactions (Marathi text appended), then verify every value
    samples = []
    for user_id in ids:
        t = time.perf_counter()
        db.execute(update(User).where(User.Id == user_id).values(FullName=func.concat(User.FullName, " (अद्यतनित)")))
        db.commit()
        samples.append(time.perf_counter() - t)
    record("UPDATE 1000 users, one transaction each", sum(samples), stats(samples))
    updated = dict(db.execute(select(User.Email, User.FullName)).all())
    assert all(updated[p.email] == p.full_name + " (अद्यतनित)" for p in people)

    # Constraints hold at scale
    with pytest.raises(IntegrityError) as dup:
        db.execute(text("INSERT INTO Users (FullName, Email, MobileNumber, PasswordHash, Role, IsActive, CreatedAt) "
                        "VALUES ('x', :e, '9099999999', 'x', 1, 1, NOW())"), {"e": people[0].email})
    assert dup.value.orig.args[0] == 1062
    db.rollback()
    with pytest.raises(IntegrityError) as fk:
        db.execute(delete(Family).where(Family.FamilyCode == people[0].ration_card))   # still referenced (RESTRICT)
    assert fk.value.orig.args[0] == 1451
    db.rollback()

    # DELETE: half, check nothing orphaned, then the rest
    half = [p.email for p in people[:500]]
    t = time.perf_counter()
    user_ids = list(db.scalars(select(User.Id).where(User.Email.in_(half))))
    family_ids = list(db.scalars(select(Beneficiary.FamilyId).where(Beneficiary.UserId.in_(user_ids))))
    db.execute(delete(User).where(User.Id.in_(user_ids)))                 # cascades: beneficiary + its verifications
    db.execute(delete(FamilyMember).where(FamilyMember.FamilyId.in_(family_ids)))
    db.execute(delete(Family).where(Family.Id.in_(family_ids)))
    db.commit()
    record("DELETE 500 citizens (cascade + families)", time.perf_counter() - t, "")
    assert _count(db, User) == 500 and _count(db, Beneficiary) == 500 and _count(db, Family) == 500
    orphans = db.scalar(select(func.count()).select_from(AadhaarVerification)
                        .outerjoin(Beneficiary, Beneficiary.Id == AadhaarVerification.BeneficiaryId).where(Beneficiary.Id.is_(None)))
    assert orphans == 0
    assert _count(db, AadhaarVerification) == _count(db, MobileVerification) == _count(db, PassbookVerification) == 500

    db.execute(delete(User))
    db.execute(delete(FamilyMember))
    db.execute(delete(Family))
    db.commit()
    assert all(_count(db, m) == 0 for m in PERSON_TABLES)
    assert _count(db, RationShop) == shops_before                   # reference data untouched


def test_connection_and_single_query_timings(engine, record):
    fresh = create_engine(engine.url, poolclass=NullPool)
    connect, query = [], []
    try:
        for _ in range(50):
            t = time.perf_counter()
            with fresh.connect() as conn:
                connect.append(time.perf_counter() - t)
                t = time.perf_counter()
                conn.execute(text("SELECT 1"))
                query.append(time.perf_counter() - t)
    finally:
        fresh.dispose()
    record("open a new MySQL connection", sum(connect), stats(connect))
    record("single trivial query", sum(query), stats(query))
    assert max(connect) < 5 and max(query) < 2


# ------------------------------------------------------------------ concurrency levels

def _people(db, count: int, seed: int, password_hash: str) -> list[int]:
    insert(db, generate(count, seed=seed), password_hash)
    db.commit()
    return list(db.scalars(select(User.Id).order_by(User.Id)))


@pytest.mark.parametrize("level", LEVELS)
def test_concurrent_reads(db, password_hash, level, record):
    people = generate(100, seed=300 + level)
    insert(db, people, password_hash)
    db.commit()

    def read(i):
        p = people[i % 100]
        with new_session() as s:
            email = s.scalar(select(User.Email).join(Beneficiary, Beneficiary.UserId == User.Id)
                             .where(Beneficiary.BeneficiaryCode == p.beneficiary_code))
        return email == p.email

    t = time.perf_counter()
    results = run_parallel(read, level, workers=level)
    record(f"{level} concurrent reads", time.perf_counter() - t, "")
    assert results == [True] * level


@pytest.mark.parametrize("level", LEVELS)
def test_concurrent_creates(db, password_hash, level, record):
    people = generate(level, seed=400 + level)

    def create(i):
        with new_session() as s, s.begin():
            insert(s, people[i:i + 1], password_hash)
        return True

    t = time.perf_counter()
    results = run_parallel(create, level, workers=level)
    record(f"{level} concurrent citizen creations", time.perf_counter() - t, "")
    assert [r for r in results if r is not True] == []
    db.rollback()
    assert _count(db, User) == _count(db, Beneficiary) == _count(db, Family) == level
    assert db.scalar(select(func.count(func.distinct(Family.FamilyCode)))) == level


def _optimistic(fn, attempts: int = 500):
    """Retry fn() while it reports a lost race (None); give up only after many attempts."""
    for _ in range(attempts):
        outcome = fn()
        if outcome is not None:
            return outcome
    return "gave up"


@pytest.fixture
def stock_row(db):
    """The first Inventory row (reference data, not wiped between tests): restored afterwards."""
    item_id, original = db.execute(select(Inventory.Id, Inventory.AvailableQuantity).order_by(Inventory.Id).limit(1)).one()
    yield item_id
    db.rollback()
    db.execute(update(Inventory).where(Inventory.Id == item_id).values(AvailableQuantity=original))
    db.commit()


@pytest.mark.parametrize("level", LEVELS)
def test_concurrent_updates_lose_nothing(db, stock_row, level):
    """`level` clients each add 1 to the same stock row with the C# optimistic check: final = start + level."""
    item_id = stock_row
    start = db.scalar(select(Inventory.AvailableQuantity).where(Inventory.Id == item_id))

    def add_one(_):
        def attempt():
            with new_session() as s, s.begin():
                seen = s.scalar(select(Inventory.AvailableQuantity).where(Inventory.Id == item_id))
                won = s.execute(update(Inventory).where(Inventory.Id == item_id, Inventory.AvailableQuantity == seen)
                                .values(AvailableQuantity=seen + 1)).rowcount
                return True if won else None
        return _optimistic(attempt)

    results = run_parallel(add_one, level, workers=level)
    db.rollback()
    assert results == [True] * level
    assert db.scalar(select(Inventory.AvailableQuantity).where(Inventory.Id == item_id)) == start + level


@pytest.mark.parametrize("level", LEVELS)
def test_concurrent_token_allocation(db, password_hash, level, record):
    """`level` citizens race for a slot with capacity level/2: exactly that many tokens, no duplicates,
    counter == tokens (the C# BookingService pattern, with the losers retrying)."""
    user_ids = _people(db, level, 500 + level, password_hash)
    capacity = level // 2
    slot = db.scalar(select(TimeSlot).order_by(TimeSlot.Id).limit(1))
    slot.Capacity, slot.BookedCount = capacity, 0
    db.commit()
    slot_id, shop_id = slot.Id, slot.RationShopId

    def book(i):
        def attempt():
            with new_session() as s, s.begin():
                booked, cap = s.execute(select(TimeSlot.BookedCount, TimeSlot.Capacity).where(TimeSlot.Id == slot_id)).one()
                if booked >= cap:
                    return "full"
                won = s.execute(update(TimeSlot).where(TimeSlot.Id == slot_id, TimeSlot.BookedCount == booked)
                                .values(BookedCount=booked + 1)).rowcount
                if not won:
                    return None                       # DbUpdateConcurrencyException in C#: try again
                token = Token(TokenNumber=f"PENDING-{i}", UserId=user_ids[i], RationShopId=shop_id, TimeSlotId=slot_id,
                              Status=CONFIRMED, CreatedAt=utc_now())
                s.add(token)
                s.flush()
                token.TokenNumber = f"SR-{token.CreatedAt:%Y}-{token.Id:06d}"
                return "booked"
        return _optimistic(attempt)

    t = time.perf_counter()
    results = run_parallel(book, level, workers=level)
    record(f"{level} concurrent bookings for {capacity} places", time.perf_counter() - t, "")
    db.rollback()
    assert results.count("booked") == capacity and results.count("full") == level - capacity
    assert db.scalar(select(TimeSlot.BookedCount).where(TimeSlot.Id == slot_id)) == capacity
    numbers = list(db.scalars(select(Token.TokenNumber).where(Token.TimeSlotId == slot_id)))
    assert len(numbers) == len(set(numbers)) == capacity
    assert not any(n.startswith("PENDING") for n in numbers)


@pytest.mark.parametrize("level", LEVELS)
def test_concurrent_stock_issue_never_goes_negative(db, stock_row, level):
    """`level` counters issue 1 unit each from stock of level/2: exactly level/2 succeed, stock ends at 0."""
    stock = Decimal(level // 2)
    item_id = stock_row
    db.execute(update(Inventory).where(Inventory.Id == item_id).values(AvailableQuantity=stock, UpdatedAt=utc_now()))
    db.commit()

    def issue(_):
        def attempt():
            with new_session() as s, s.begin():
                seen = s.scalar(select(Inventory.AvailableQuantity).where(Inventory.Id == item_id))
                if seen < 1:
                    return "insufficient"
                won = s.execute(update(Inventory).where(Inventory.Id == item_id, Inventory.AvailableQuantity == seen)
                                .values(AvailableQuantity=seen - 1)).rowcount
                return "issued" if won else None
        return _optimistic(attempt)

    results = run_parallel(issue, level, workers=level)
    db.rollback()
    assert results.count("issued") == level // 2 and results.count("insufficient") == level - level // 2
    assert db.scalar(select(Inventory.AvailableQuantity).where(Inventory.Id == item_id)) == 0
