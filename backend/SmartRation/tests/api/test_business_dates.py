"""Every "today" / "this month" on the shops' clock (2026-10-17, Phase 3 P3-03), through the real routes on SQLite.

Rules unchanged; only the clock they are measured on: a QR is valid through its booked day, a token can be collected
until its booked day has ended, dashboards count today's bookings and today's distribution, and the monthly
entitlement is the calendar month — all in Asia/Kolkata. Before the fix these used the UTC date, which lags the Indian
date until 05:30. Fixture slot 1 = `today` 09:00 at shop 1 (ration_world). Each test pins the clock to IST instants."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from ration_world import book, qr_payload, session
from sqlalchemy import select

import app.utils.time as clock
from app.database.models import Beneficiary, RationCollection, TimeSlot, Token, User
from app.services import (
    ai_rules_service,
    booking_service,
    entitlement_service,
    government_service,
    profile_service,
    public_help_service,
    qr_service,
    shop_service,
    slot_service,
    verification_service,
)

CLOCK_READERS = (clock, booking_service, slot_service, qr_service, shop_service, government_service, verification_service,
                 entitlement_service, ai_rules_service, profile_service, public_help_service)

IST = timedelta(hours=5, minutes=30)


@pytest.fixture
def at(env, monkeypatch):
    """at(hours, minutes): pin every clock the code reads to that IST time on the fixture's `today` (may exceed 24 h)."""
    with session() as db:
        today = db.get(TimeSlot, 1).SlotDate

    def pin(hours: int, minutes: int = 0) -> datetime:
        ist = today + timedelta(hours=hours, minutes=minutes)
        utc = ist - IST
        for module in CLOCK_READERS:   # including a module's own `from app.utils.time import utc_now`
            monkeypatch.setattr(module, "utc_now", lambda: utc, raising=False)
        return ist
    return pin


def _collect(env, token_id: int):
    return env["client"].post("/api/ration/collection/confirm", headers={**env["shop"], "Idempotency-Key": f"k-{token_id}"},
                              json={"tokenId": token_id, "verificationMethod": "QR"})


def _scan(env, payload: str) -> str:
    return env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": payload}).json()["data"]["status"]


# ---------------------------------------------------------------- QR expiry: through the end of the booked IST day

def test_qr_expires_at_the_end_of_the_booked_ist_day(env, at):
    today = at(8, 0).replace(hour=0)
    token = book(env).json()["data"]
    payload = qr_payload(env, token["id"])
    end_of_day_utc = today + timedelta(days=1) - IST
    assert f'"expiresAt":"{end_of_day_utc:%Y-%m-%dT%H:%M:%S}Z"' in payload    # 18:30Z = midnight IST
    at(23, 59)
    assert _scan(env, payload) == "VERIFIED"
    at(24, 0)                                                                # the booked day is over in India
    assert _scan(env, payload) == "EXPIRED"                                  # was accepted until 05:30 IST


# ---------------------------------------------------------------- collection: until the booked IST day has ended

def test_a_token_cannot_be_collected_after_its_ist_day_even_while_the_utc_date_is_unchanged(env, at):
    at(8, 0)
    token = book(env).json()["data"]
    at(25, 30)                                                               # 01:30 IST next day; UTC date unchanged
    r = _collect(env, token["id"])
    assert r.status_code == 409 and r.json()["message"] == "This token has expired — the booked collection date has passed."
    at(23, 0)                                                                # same IST day, late evening: still fine
    assert _collect(env, token["id"]).status_code == 200


# ---------------------------------------------------------------- dashboards: today's IST date

def test_dashboards_count_todays_ist_bookings_before_0530(env, at):
    at(8, 0)
    book(env)
    at(0, 30)                                                                # 00:30 IST; the UTC date is still yesterday
    shop = env["client"].get("/api/shop/dashboard", headers=env["shop"]).json()["data"]
    assert shop["todayTotalTokens"] == 1
    official = env["client"].get("/api/admin/dashboard", headers=env["official"])
    assert official.status_code == 200 and official.json()["data"]["todayBookings"] == 1


def test_distributed_today_counts_collections_since_ist_midnight(env, at):
    today = at(8, 0).replace(hour=0)
    token = book(env).json()["data"]
    assert _collect(env, token["id"]).status_code == 200
    with session() as db:                                                    # collected at 01:00 IST = 19:30 UTC the day before
        db.get(Token, token["id"]).CollectedAt = today + timedelta(hours=1) - IST
        db.commit()
    at(10, 0)
    data = env["client"].get("/api/admin/dashboard", headers=env["official"]).json()["data"]
    assert data["rationDistributedTodayKg"] == 8                             # 5 kg rice + 3 kg wheat


# ---------------------------------------------------------------- entitlement: the IST calendar month

@pytest.fixture
def collected(env, at):
    """One completed collection (5 kg rice + 3 kg wheat); returns a function that moves it to a UTC instant."""
    at(8, 0)
    token = book(env).json()["data"]
    assert _collect(env, token["id"]).status_code == 200
    with session() as db:
        family_id = db.scalar(select(Beneficiary.FamilyId).join(User, User.Id == Beneficiary.UserId)
                              .where(User.Email == "asha@example.com"))

    def move_to(utc: datetime) -> int:
        with session() as db:
            db.scalar(select(RationCollection)).CollectedAt = utc
            db.commit()
        return family_id
    return move_to


def _rice_collected(monkeypatch, family_id: int, now_utc: datetime) -> float:
    monkeypatch.setattr(clock, "utc_now", lambda: now_utc)
    with session() as db:
        items = entitlement_service.get_entitlement(db, family_id)["items"]
    return next(i["alreadyCollected"] for i in items if i["rationType"] == "Rice")


def test_a_collection_at_0130_ist_on_the_1st_counts_in_the_new_month(collected, monkeypatch):
    family = collected(datetime(2026, 10, 31, 20, 0))                       # 1 Nov 01:30 IST
    assert _rice_collected(monkeypatch, family, datetime(2026, 11, 1, 0, 0)) == 5      # 1 Nov 05:30 IST: November's
    assert _rice_collected(monkeypatch, family, datetime(2026, 10, 31, 18, 0)) == 0    # 31 Oct 23:30 IST: not October's


def test_on_the_1st_before_0530_ist_last_months_collections_no_longer_count(collected, monkeypatch):
    family = collected(datetime(2026, 10, 31, 18, 0))                       # 31 Oct 23:30 IST
    assert _rice_collected(monkeypatch, family, datetime(2026, 10, 31, 19, 0)) == 0    # 1 Nov 00:30 IST: a new month
    assert _rice_collected(monkeypatch, family, datetime(2026, 10, 31, 18, 15)) == 5   # 31 Oct 23:45 IST: same month
