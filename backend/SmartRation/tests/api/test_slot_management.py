"""Time-slot management (POST /api/slots, PUT /api/slots/{id}): who may manage which shop's slots, and the slot rules.

Added 2026-10-18: coverage showed no test reached slot creation or capacity changes, including the check that a shop
owner can only manage their own shop's slots (officials may manage any shop's).
"""

from __future__ import annotations

from datetime import timedelta

from ration_world import book

from app.utils import time as clock


def _day(offset: int = 1) -> str:
    return f"{clock.business_today() + timedelta(days=offset):%Y-%m-%d}"


def _create(env, headers, shop_id=1, start="10:00:00", end="10:05:00", capacity=3, day=None):
    return env["client"].post("/api/slots", headers=headers, json={
        "rationShopId": shop_id, "slotDate": day or _day(), "startTime": start, "endTime": end, "capacity": capacity})


def test_a_shop_owner_creates_slots_for_their_own_shop(env):
    r = _create(env, env["shop"])
    assert r.status_code == 200, r.text
    slot = r.json()["data"]
    assert (slot["startTime"], slot["endTime"], slot["capacity"]) == ("10:00:00", "10:05:00", 3)
    listed = env["client"].get("/api/slots", headers=env["citizen"], params={"shopId": 1, "date": _day()}).json()["data"]
    assert slot["id"] in [s["id"] for s in listed]


def test_nobody_manages_another_shops_slots(env):
    r = _create(env, env["other_shop"], shop_id=1)
    assert r.status_code == 403
    assert _create(env, env["citizen"]).status_code == 403                       # citizens: staff only
    r = env["client"].put("/api/slots/2", headers=env["other_shop"], json={"capacity": 9})
    assert r.status_code == 403
    assert env["client"].put("/api/slots/2", headers=env["citizen"], json={"capacity": 9}).status_code == 403


def test_an_official_may_manage_any_shop(env):
    assert _create(env, env["official"], shop_id=2).status_code == 200
    r = env["client"].put("/api/slots/2", headers=env["official"], json={"capacity": 7})
    assert r.status_code == 200 and r.json()["data"]["capacity"] == 7


def test_slot_rules(env):
    assert _create(env, env["shop"], start="10:05:00", end="10:00:00").status_code == 400     # ends before it starts
    assert _create(env, env["shop"], start="09:02:00", end="09:07:00").status_code == 409     # overlaps slot 2 (09:00-09:05)
    assert _create(env, env["shop"], shop_id=99).status_code in (403, 404)                    # no such shop (not theirs)
    assert _create(env, env["official"], shop_id=99).status_code == 404
    assert _create(env, env["shop"], capacity=0).status_code == 400
    assert _create(env, env["shop"], capacity=501).status_code == 400


def test_capacity_changes_respect_existing_bookings(env):
    assert book(env, slot_id=2, items=[{"rationType": "Rice", "quantity": 1}]).status_code == 200   # slot 2: 1 booked
    r = env["client"].put("/api/slots/2", headers=env["shop"], json={"capacity": 4})
    assert r.status_code == 200 and r.json()["data"]["capacity"] == 4
    assert env["client"].put("/api/slots/999", headers=env["shop"], json={"capacity": 4}).status_code == 404
    assert env["client"].put("/api/slots/2", headers=env["shop"], json={"capacity": 0}).status_code == 400
