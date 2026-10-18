"""Duplicate-collection protection on real MySQL (2026-10-17, DEF-05).

A citizen registers and books through the real API; then several shop counters confirm the SAME token at the same
moment through the real collection service, each on its own connection and transaction. Exactly one collection may
succeed, stock must move exactly once, and a failure inside the transaction must leave nothing behind.
The protection under test: the token row lock (SELECT ... FOR UPDATE + status re-check) and the unique
RationCollections.TokenId / IdempotencyKey keys. Runs only against a *_test database (see conftest.py)."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.api.dependencies.auth import Actor
from app.core.errors import ApiError
from app.database.enums import InventoryMovementType, TokenStatus, UserRole
from app.database.models import (
    Beneficiary,
    Family,
    Inventory,
    InventoryMovement,
    RationCollection,
    TimeSlot,
    Token,
    TokenItem,
    User,
)
from app.security.tokens import TokenUser, create_access_token
from app.services import audit_service, collection_service
from app.utils.time import business_today, utc_now
from mysql_suite.support import new_session

COUNTERS = 8
PASSWORD = "Kite-River-Lamp-42"   # test-only value for a synthetic citizen


def run_parallel(fn, count: int) -> list:
    """fn(i) on `count` threads released together; each result or the exception it raised."""
    gate = threading.Barrier(count)

    def safe(i):
        gate.wait()
        try:
            return fn(i)
        except Exception as exc:  # collected, asserted on by the caller
            return exc
    with ThreadPoolExecutor(max_workers=count) as pool:
        return list(pool.map(safe, range(count)))


@pytest.fixture
def booked(api, db, password_hash):
    """A synthetic citizen with one confirmed booking (rice + wheat) for tomorrow, and that shop's owner."""
    r = api.post("/api/auth/register", json={"fullName": "Race Citizen", "email": "race@example.test", "mobileNumber": "7000000101",
                                             "password": PASSWORD, "consentToPrivacyPolicy": True})
    assert r.status_code == 200, r.text
    citizen = db.scalar(select(User).where(User.Email == "race@example.test"))
    shop_id = db.scalar(select(Family.RationShopId).join(Beneficiary, Beneficiary.FamilyId == Family.Id)
                        .where(Beneficiary.UserId == citizen.Id))
    owner = User(FullName="Race Shop", Email="race-shop@example.test", MobileNumber="7000000102", PasswordHash=password_hash,
                 Role=int(UserRole.ShopOwner), RationShopId=shop_id, IsActive=True, CreatedAt=utc_now())
    slot = TimeSlot(RationShopId=shop_id, SlotDate=business_today() + timedelta(days=1), StartTime=time(10), EndTime=time(10, 5),
                    Capacity=5, BookedCount=0)
    db.add_all([owner, slot])
    # Inventory is reference data that wipe() keeps, so every collection here would lower it for good and repeated
    # runs would end in "insufficient stock". Start each test from known stock and put the original back afterwards.
    shelves = list(db.scalars(select(Inventory).where(Inventory.RationShopId == shop_id)))
    original = {i.Id: i.AvailableQuantity for i in shelves}
    for item in shelves:
        item.AvailableQuantity = Decimal(100)
    db.commit()

    settings = api.app.state.settings
    bearer = create_access_token(TokenUser(citizen.Id, citizen.Email, citizen.FullName, "RuralUser", None), settings)[0]
    r = api.post("/api/ration/bookings", headers={"Authorization": f"Bearer {bearer}"}, json={
        "rationShopId": shop_id, "timeSlotId": slot.Id,
        "items": [{"rationType": "Rice", "quantity": 2}, {"rationType": "Wheat", "quantity": 1}]})
    assert r.status_code == 200, r.text
    token_id = r.json()["data"]["id"]
    db.rollback()   # fresh snapshot
    stock = {i.RationType: i.AvailableQuantity for i in db.scalars(select(Inventory).where(Inventory.RationShopId == shop_id))}
    requested = {i.RationType: i.Quantity for i in db.scalars(select(TokenItem).where(TokenItem.TokenId == token_id))}
    yield {"token_id": token_id, "shop_id": shop_id, "stock": stock, "requested": requested,
           "actor": Actor(user_id=owner.Id, role=UserRole.ShopOwner, ration_shop_id=shop_id)}
    db.rollback()
    for item in db.scalars(select(Inventory).where(Inventory.Id.in_(original))):
        item.AvailableQuantity = original[item.Id]
    db.commit()


def _confirm(world, key: str | None):
    with new_session() as s:
        return collection_service.confirm(s, world["actor"], world["token_id"], "QR", key)


def _state(db, world) -> dict:
    db.rollback()   # end this session's REPEATABLE-READ snapshot so the workers' commits are visible
    token = db.get(Token, world["token_id"])
    return {
        "status": token.Status,
        "collections": db.scalar(select(func.count()).select_from(RationCollection).where(RationCollection.TokenId == token.Id)),
        "stock": {i.RationType: i.AvailableQuantity for i in db.scalars(select(Inventory).where(Inventory.RationShopId == world["shop_id"]))},
        "distributed": db.scalar(select(func.count()).select_from(InventoryMovement).where(
            InventoryMovement.Reference == token.TokenNumber, InventoryMovement.MovementType == int(InventoryMovementType.Distributed))),
    }


def _issued_once(world) -> dict:
    return {t: q - world["requested"].get(t, Decimal(0)) for t, q in world["stock"].items()}


def test_same_token_confirmed_by_many_counters_at_once_is_collected_exactly_once(db, booked):
    results = run_parallel(lambda i: _confirm(booked, f"race-{i}"), COUNTERS)   # different requests

    receipts = [r for r in results if isinstance(r, dict)]
    refusals = [r for r in results if isinstance(r, ApiError)]
    unexpected = [r for r in results if not isinstance(r, (dict, ApiError))]
    assert unexpected == [], unexpected
    assert len(receipts) == 1 and len(refusals) == COUNTERS - 1
    assert all(r.status_code == 409 for r in refusals)          # "already used" or CONCURRENT_UPDATE, never 500
    state = _state(db, booked)
    assert state["status"] == TokenStatus.Completed and state["collections"] == 1
    assert state["stock"] == _issued_once(booked)                # each item deducted exactly once
    assert state["distributed"] == len(booked["requested"])      # one ledger row per item, not per attempt


def test_the_same_request_retried_concurrently_returns_one_receipt(db, booked):
    results = run_parallel(lambda _: _confirm(booked, "retry-key-1"), COUNTERS)

    receipts = [r for r in results if isinstance(r, dict)]
    assert [r for r in results if not isinstance(r, (dict, ApiError))] == []
    assert receipts and len({r["collectionCode"] for r in receipts}) == 1   # retries see the first receipt, or a 409
    state = _state(db, booked)
    assert state["collections"] == 1 and state["stock"] == _issued_once(booked)


def test_a_failure_inside_the_transaction_leaves_nothing_and_a_retry_succeeds_once(db, booked, monkeypatch):
    def broken(*_args, **_kwargs):
        raise RuntimeError("simulated failure after stock was deducted in the transaction")

    monkeypatch.setattr(audit_service, "record", broken)
    with pytest.raises(RuntimeError):
        _confirm(booked, "fails-1")
    state = _state(db, booked)
    assert state["status"] == TokenStatus.Confirmed and state["collections"] == 0
    assert state["stock"] == booked["stock"] and state["distributed"] == 0   # rolled back: nothing issued

    monkeypatch.undo()
    assert _confirm(booked, "after-fix-1")["collectionCode"].startswith("COL-DEMO-")
    state = _state(db, booked)
    assert state["collections"] == 1 and state["stock"] == _issued_once(booked)


# ---------------------------------------------------------------- two application instances (Phase 3, P3-06)
# Production may run more than one copy of the API. The protections above must hold across processes, i.e. come from
# the database (row locks, unique keys), not from anything in one process's memory. A second engine with its own
# connection pool stands in for a second instance.

@pytest.fixture
def two_instances(engine, test_url):
    from sqlalchemy.orm import sessionmaker

    from app.database.connection import _build_engine
    second = _build_engine(test_url)
    other = sessionmaker(bind=second, autoflush=False, expire_on_commit=False)
    yield lambda i: new_session() if i % 2 == 0 else other()   # even workers on instance A, odd on instance B
    second.dispose()


def test_same_token_from_two_instances_is_collected_exactly_once(db, booked, two_instances):
    def attempt(i):
        with two_instances(i) as s:
            return collection_service.confirm(s, booked["actor"], booked["token_id"], "QR", f"inst-{i}")

    results = run_parallel(attempt, COUNTERS)
    assert [r for r in results if not isinstance(r, (dict, ApiError))] == []
    assert len([r for r in results if isinstance(r, dict)]) == 1
    state = _state(db, booked)
    assert state["collections"] == 1 and state["stock"] == _issued_once(booked) and state["distributed"] == len(booked["requested"])


def test_a_delivery_retried_concurrently_from_two_instances_is_recorded_once(db, booked, two_instances):
    from app.services import inventory_service

    rice = db.scalar(select(Inventory).where(Inventory.RationShopId == booked["shop_id"], Inventory.RationType == 1))
    before = rice.AvailableQuantity

    def deliver(i):
        with two_instances(i) as s:
            return inventory_service.receive(s, booked["actor"], rice.Id, Decimal("10"), "DELIVERY-1", None, "delivery-key-1")

    results = run_parallel(deliver, COUNTERS)
    assert [r for r in results if not isinstance(r, (dict, ApiError))] == []
    assert all(r.status_code == 409 for r in results if isinstance(r, ApiError))   # a lost race says "try again", never 500
    db.rollback()
    assert db.scalar(select(Inventory.AvailableQuantity).where(Inventory.Id == rice.Id)) == before + 10   # once, not 8 times
    assert db.scalar(select(func.count()).select_from(InventoryMovement).where(InventoryMovement.IdempotencyKey == "delivery-key-1")) == 1


def test_counter_code_daily_limit_holds_under_concurrent_requests_from_two_instances(db, booked, two_instances, test_url):
    """Phase 3 Q2: 8 shop-counter code requests for one citizen at the same moment, split over two application
    instances, with OTP_COUNTER_DAILY_LIMIT=3 (cool-down off): exactly 3 codes are issued, the rest get 429."""
    from app.config.settings import Settings
    from app.database.models import OtpVerification
    from app.services import otp_service
    from mysql_suite.support import KEY, QR_TEST_SECRET

    settings = Settings(_env_file=None, database_url=test_url, legacy_api_url="", jwt_secret_key=KEY, qr_secret=QR_TEST_SECRET,
                        ai_service_url="", otp_resend_cooldown_seconds=0, otp_counter_daily_limit=3)
    beneficiary_id = db.scalar(select(Token.UserId).where(Token.Id == booked["token_id"]))
    beneficiary_id = db.scalar(select(Beneficiary.Id).where(Beneficiary.UserId == beneficiary_id))

    def ask(i):
        with two_instances(i) as s:
            return otp_service.request(s, settings, beneficiary_id, booked["actor"].user_id).Id

    results = run_parallel(ask, COUNTERS)
    issued = [r for r in results if isinstance(r, int)]
    refused = [r for r in results if isinstance(r, ApiError)]
    assert [r for r in results if not isinstance(r, (int, ApiError))] == []          # no deadlock, no 500
    assert len(issued) == 3 and len(refused) == COUNTERS - 3
    assert {(r.status_code, r.error_code) for r in refused} == {(429, "OTP_DAILY_LIMIT")}
    db.rollback()
    assert db.scalar(select(func.count()).select_from(OtpVerification).where(OtpVerification.BeneficiaryId == beneficiary_id)) == 3


def test_counter_codes_around_midnight_in_india_count_towards_the_right_day(db, booked, two_instances, test_url, monkeypatch):
    """Phase 5: the daily limit resets at 00:00 Asia/Kolkata, also under concurrency. Yesterday's 3 codes (the limit)
    are on record; 8 requests arrive together across two instances, half at 23:59:59 IST and half at 00:00:01 IST.
    Every late-evening request is refused; of the after-midnight ones exactly 3 are issued (a fresh day's limit)."""
    from datetime import datetime

    from app.config.settings import Settings
    from app.database.models import OtpVerification
    from app.services import otp_service
    from app.utils import time as clock
    from mysql_suite.support import KEY, QR_TEST_SECRET

    settings = Settings(_env_file=None, database_url=test_url, legacy_api_url="", jwt_secret_key=KEY, qr_secret=QR_TEST_SECRET,
                        ai_service_url="", otp_resend_cooldown_seconds=0, otp_counter_daily_limit=3)
    citizen = db.scalar(select(Token.UserId).where(Token.Id == booked["token_id"]))
    beneficiary_id = db.scalar(select(Beneficiary.Id).where(Beneficiary.UserId == citizen))
    midnight_utc = datetime(2026, 10, 16, 18, 30)                              # 17 Oct 00:00 IST
    worker_clock = threading.local()
    for module in (clock, otp_service):
        monkeypatch.setattr(module, "utc_now", lambda: getattr(worker_clock, "now", midnight_utc - timedelta(minutes=10)))

    with new_session() as s:                                                     # 16 Oct 23:50 IST: the day's limit
        for _ in range(3):
            otp_service.request(s, settings, beneficiary_id, booked["actor"].user_id)

    def ask(i):
        group = "after" if i % 4 >= 2 else "before"
        worker_clock.now = midnight_utc + (timedelta(seconds=1) if group == "after" else timedelta(seconds=-1))
        with two_instances(i) as s:
            try:
                return group, otp_service.request(s, settings, beneficiary_id, booked["actor"].user_id).Id
            except ApiError as refused:
                return group, (refused.status_code, refused.error_code)

    results = run_parallel(ask, COUNTERS)
    assert [r for r in results if not isinstance(r, tuple)] == []                # no deadlock, no 500
    issued = [group for group, outcome in results if isinstance(outcome, int)]
    assert issued == ["after"] * 3                                               # never on yesterday's spent limit
    # A 23:59:59 request handled just after a 00:00:01 code was saved sees that code as "newer" and may meet the
    # cool-down instead of the limit; either way it is refused.
    assert {o for g, o in results if g == "before"} <= {(429, "OTP_DAILY_LIMIT"), (400, "OTP_COOLDOWN")}
    assert [o for g, o in results if g == "after" and not isinstance(o, int)] == [(429, "OTP_DAILY_LIMIT")]
    db.rollback()
    created = db.scalars(select(OtpVerification.CreatedAt).where(OtpVerification.BeneficiaryId == beneficiary_id)).all()
    assert sorted(at >= midnight_utc for at in created) == [False] * 3 + [True] * 3
