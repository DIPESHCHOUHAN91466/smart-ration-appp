"""Concurrency: many connections at once. No lost updates, no overbooking, no duplicates,
deadlocks detected and retried, the pool queues instead of failing."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.errors import ApiError
from app.database.models import Beneficiary, Family, TimeSlot, User
from app.services import auth_service
from app.services.auth_service import RequestContext
from mysql_suite.sample_data import people
from mysql_suite.support import KEY, QR_TEST_SECRET, new_session

THREADS = 20


def run_parallel(fn, count: int, workers: int = THREADS) -> list:
    """Run fn(i) for i in range(count) on `workers` threads; return results or exceptions."""
    def safe(i):
        try:
            return fn(i)
        except Exception as exc:  # collected, asserted on by the caller
            return exc
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(safe, range(count)))


def first_slot_id(db) -> int:
    return db.scalar(select(TimeSlot.Id).order_by(TimeSlot.Id).limit(1))


def test_no_lost_updates_with_row_locks(db):
    """100 concurrent increments of one counter using SELECT ... FOR UPDATE end at exactly 100."""
    slot_id = first_slot_id(db)

    def increment(_):
        with new_session() as s, s.begin():
            slot = s.scalar(select(TimeSlot).where(TimeSlot.Id == slot_id).with_for_update())
            slot.BookedCount += 1

    errors = [r for r in run_parallel(increment, 100) if isinstance(r, Exception)]
    db.rollback()  # end this session's REPEATABLE-READ snapshot so it sees the threads' commits
    assert errors == []
    assert db.scalar(select(TimeSlot.BookedCount).where(TimeSlot.Id == slot_id)) == 100


def test_capacity_is_never_exceeded(db):
    """30 people race for a slot with capacity 2: exactly 2 get it."""
    slot_id = first_slot_id(db)

    def book(_):
        with new_session() as s, s.begin():
            slot = s.scalar(select(TimeSlot).where(TimeSlot.Id == slot_id).with_for_update())
            if slot.BookedCount >= slot.Capacity:
                return False
            time.sleep(0.01)                  # widen the race window on purpose
            slot.BookedCount += 1
            return True

    results = run_parallel(book, 30)
    db.rollback()  # end this session's REPEATABLE-READ snapshot so it sees the threads' commits
    assert results.count(True) == 2 and results.count(False) == 28
    assert db.scalar(select(TimeSlot.BookedCount).where(TimeSlot.Id == slot_id)) == 2


def test_duplicate_insert_race_creates_exactly_one_row(db, make_user):
    def insert_same(i):
        with new_session() as s:
            s.add(make_user("race@example.test", f"72000000{i:02d}"))
            s.commit()
            return True

    results = run_parallel(insert_same, 20)
    assert results.count(True) == 1
    assert all(isinstance(r, IntegrityError) and r.orig.args[0] == 1062 for r in results if r is not True)
    assert db.scalar(select(func.count()).select_from(User)) == 1


def _ctx() -> RequestContext:
    return RequestContext(ip_address="127.0.0.1")


@pytest.fixture
def settings(test_url):
    from app.config.settings import Settings
    return Settings(_env_file=None, database_url=test_url, legacy_api_url="", jwt_secret_key=KEY, qr_secret=QR_TEST_SECRET,
                    ai_service_url="")


def test_100_concurrent_registrations(db, settings):
    """100 different people register at the same time: 100 users, 100 beneficiaries, 100 families,
    all codes unique, nothing half-created."""
    group = people("conc")

    def register(i):
        p = group[i]
        with new_session() as s:
            auth_service.register(s, settings, _ctx(), p.full_name, p.email, p.mobile, p.password)
        return True

    results = run_parallel(register, 100, workers=10)
    failures = [r for r in results if r is not True]
    assert failures == []
    db.rollback()  # end this session's REPEATABLE-READ snapshot so it sees the threads' commits
    assert db.scalar(select(func.count()).select_from(User)) == 100
    assert db.scalar(select(func.count(func.distinct(Beneficiary.BeneficiaryCode)))) == 100
    assert db.scalar(select(func.count(func.distinct(Family.FamilyCode)))) == 100
    assert db.scalar(select(func.count()).select_from(Beneficiary).where(Beneficiary.BeneficiaryCode == "")) == 0


def test_same_person_registering_twice_at_once(db, settings):
    def register(_):
        with new_session() as s:
            auth_service.register(s, settings, _ctx(), "Twin", "twin@example.test", "7300000000", "Valid-Pass-1")
        return True

    results = run_parallel(register, 10)
    assert results.count(True) == 1
    assert all(isinstance(r, ApiError) and r.status_code == 409 for r in results if r is not True)
    assert db.scalar(select(func.count()).select_from(User)) == 1
    assert db.scalar(select(func.count()).select_from(Beneficiary)) == 1  # no orphaned half-registration


def _lock_two_rows(first: int, second: int, barrier: threading.Barrier, retry: bool) -> str:
    for attempt in range(3):
        try:
            with new_session() as s, s.begin():
                s.execute(text("SELECT Id FROM TimeSlots WHERE Id = :i FOR UPDATE"), {"i": first})
                if attempt == 0:
                    barrier.wait(timeout=10)          # both hold their first lock before taking the second
                s.execute(text("SELECT Id FROM TimeSlots WHERE Id = :i FOR UPDATE"), {"i": second})
                s.execute(text("UPDATE TimeSlots SET BookedCount = BookedCount + 1 WHERE Id IN (:a, :b)"), {"a": first, "b": second})
            return "committed" if attempt == 0 else "committed after retry"
        except OperationalError as exc:
            if exc.orig.args[0] != 1213 or not retry:   # 1213 = deadlock found
                return f"error {exc.orig.args[0]}"
    return "gave up"


@pytest.mark.parametrize("retry", [False, True])
def test_deadlock_is_detected_and_retry_recovers(db, retry):
    a, b = db.scalars(select(TimeSlot.Id).order_by(TimeSlot.Id).limit(2)).all()
    barrier = threading.Barrier(2)
    with ThreadPoolExecutor(2) as pool:
        outcomes = sorted(f.result() for f in [pool.submit(_lock_two_rows, a, b, barrier, retry),
                                               pool.submit(_lock_two_rows, b, a, barrier, retry)])
    db.rollback()  # end this session's REPEATABLE-READ snapshot so it sees the threads' commits
    counts = db.execute(select(TimeSlot.BookedCount).where(TimeSlot.Id.in_([a, b]))).scalars().all()
    if retry:
        assert outcomes == ["committed", "committed after retry"]
        assert counts == [2, 2]                     # both transactions applied, exactly once each
    else:
        assert outcomes == ["committed", "error 1213"]  # MySQL broke the deadlock instantly, no hang
        assert counts == [1, 1]                     # the victim was rolled back completely


def test_pool_queues_more_threads_than_connections(engine):
    """40 threads, pool of 10 + 10 overflow: extra threads wait for a connection, none fail."""
    def hold(_):
        with engine.connect() as conn:
            conn.execute(text("SELECT SLEEP(0.2)"))
        return True

    start = time.perf_counter()
    results = run_parallel(hold, 40, workers=40)
    assert results == [True] * 40
    assert time.perf_counter() - start < 10
    assert engine.pool.checkedout() == 0            # every connection went back to the pool
