"""Booking against the shops' clock (2026-10-17, DEF-03), through the real routes on SQLite.

Before the fix the backend compared only the UTC date: a slot that had already started today was bookable, and between
00:00 and 05:30 IST yesterday's slots were too. Fixture slots (ration_world): 1 = today 09:00, 2 = tomorrow 09:00,
3 = yesterday 09:00, all at shop 1; shop 2 has none. Each test pins the shops' clock to one instant."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from ration_world import book, session
from sqlalchemy import select

import app.utils.time as clock
from app.database.models import TimeSlot
from app.services import booking_service, slot_service

PAST = "Cannot book a time slot in the past."


@pytest.fixture
def at(env, monkeypatch):
    """at(hours, minutes): pin the shops' clock to that IST time on the fixture's `today` (may be negative/over 24 h)."""
    with session() as db:
        today = db.get(TimeSlot, 1).SlotDate

    def pin(hours: int, minutes: int = 0) -> datetime:
        ist = today + timedelta(hours=hours, minutes=minutes)
        utc = ist - timedelta(hours=5, minutes=30)
        # every clock the booking code can read, including a module's own `from app.utils.time import utc_now`
        for module in (clock, booking_service, slot_service):
            monkeypatch.setattr(module, "utc_now", lambda: utc, raising=False)
        return ist
    return pin


def test_a_future_slot_today_is_bookable(env, at):
    at(8, 0)
    assert book(env, slot_id=1).status_code == 200


def test_a_slot_starting_exactly_now_is_refused(env, at):
    at(9, 0)
    r = book(env, slot_id=1)
    assert r.status_code == 400 and r.json()["message"] == PAST


def test_a_slot_that_started_earlier_today_is_refused(env, at):
    at(13, 0)
    r = book(env, slot_id=1)
    assert r.status_code == 400 and r.json()["message"] == PAST
    assert book(env, slot_id=2).status_code == 200            # tomorrow's slot is still fine


def test_yesterdays_slot_is_refused_while_the_utc_date_is_still_yesterday(env, at):
    at(1, 30)                                                  # 01:30 IST = 20:00 UTC the previous day
    r = book(env, slot_id=3)
    assert r.status_code == 400 and r.json()["message"] == PAST


def test_shortly_after_midnight_todays_slots_are_bookable(env, at):
    at(0, 1)                                                   # 00:01 IST, UTC date is still yesterday
    assert book(env, slot_id=1).status_code == 200


@pytest.mark.parametrize(("hours", "minutes"), [(5, 29), (5, 30), (5, 31)])
def test_around_05_30_ist_the_rules_do_not_change(env, at, hours, minutes):
    at(hours, minutes)                                         # UTC date flips at 05:30 IST
    assert book(env, slot_id=3).json()["message"] == PAST
    assert book(env, slot_id=1).status_code == 200


def test_reschedule_into_a_started_slot_is_refused_and_into_a_future_one_allowed(env, at):
    at(8, 0)
    token = book(env, slot_id=1).json()["data"]
    at(10, 0)
    move = lambda slot: env["client"].put(f"/api/ration/bookings/{token['id']}", headers=env["citizen"],  # noqa: E731
                                          json={"timeSlotId": slot})
    r = move(3)
    assert r.status_code == 400 and r.json()["message"] == "Cannot reschedule to a time slot in the past."
    assert move(2).status_code == 200


def test_demo_slots_are_generated_from_the_ist_date(env, at):
    today = at(1, 0).replace(hour=0, minute=0)                # 01:00 IST: the UTC date is still yesterday
    with session() as db:
        assert slot_service.ensure_upcoming(db, days=1) > 0
        days = set(db.scalars(select(TimeSlot.SlotDate).where(TimeSlot.RationShopId == 2)).all())
    assert days == {today}
