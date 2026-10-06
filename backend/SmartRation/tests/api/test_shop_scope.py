"""Object-level access for shop owners (security N2): a shop sees the families registered at it and the citizens
who booked at it — not every citizen by guessing sequential ids. Officials see everyone; citizens only themselves."""

from __future__ import annotations

from datetime import time

import pytest
from sqlalchemy import select

from app.database.connection import get_session_factory
from app.database.enums import TokenStatus
from app.database.models import Beneficiary, TimeSlot, Token, User
from app.utils.time import utc_now

ROUTES = [
    "/api/beneficiaries/{b}/full-profile",
    "/api/beneficiaries/{b}/verification",
    "/api/beneficiaries/{b}/family",
    "/api/beneficiaries/{b}/entitlement",
    "/api/beneficiaries/{b}/collections",
    "/api/ration/collection/history/{b}",
    "/api/ai/beneficiaries/{b}/insight",
    "/api/families/{f}",
    "/api/families/{f}/entitlement",
]


def asha(env) -> tuple[int, int]:
    with get_session_factory()() as db:
        b = db.scalar(select(Beneficiary).join(User, User.Id == Beneficiary.UserId).where(User.Email == "asha@example.com"))
        return b.Id, b.FamilyId


def statuses(env, who):
    b, f = asha(env)
    return {route: env["client"].get(route.format(b=b, f=f), headers=env[who]).status_code for route in ROUTES}


def test_the_home_shop_and_officials_see_the_citizen(env):
    for who in ("shop", "official"):
        assert set(statuses(env, who).values()) == {200}, who


def test_another_shop_cannot_read_a_citizen_it_never_served(env):
    assert set(statuses(env, "other_shop").values()) == {403}


def test_another_shop_can_once_the_citizen_books_there(env):
    with get_session_factory()() as db:                                  # a booking at shop 2 (portability)
        user_id = db.scalar(select(User.Id).where(User.Email == "asha@example.com"))
        db.add(TimeSlot(Id=20, RationShopId=2, SlotDate=utc_now().date(), StartTime=time(23, 50), EndTime=time(23, 55),
                        Capacity=2, BookedCount=1))
        db.add(Token(TokenNumber="SR-TEST-2", UserId=user_id, RationShopId=2, TimeSlotId=20, Status=int(TokenStatus.Confirmed),
                     CreatedAt=utc_now()))
        db.commit()
    assert set(statuses(env, "other_shop").values()) == {200}           # ration portability: the shop serving them


@pytest.mark.parametrize("route", ROUTES)
def test_a_citizen_still_cannot_read_someone_else(env, route):
    r = env["client"].post("/api/auth/register", json={"fullName": "Ravi Kale", "email": "ravi@example.com",
                                                       "mobileNumber": "9000000002", "password": "Kite-River-Lamp-42"})
    assert r.status_code == 200, r.text
    with get_session_factory()() as db:
        other = db.scalar(select(Beneficiary).join(User, User.Id == Beneficiary.UserId).where(User.Email == "ravi@example.com"))
    r = env["client"].get(route.format(b=other.Id, f=other.FamilyId), headers=env["citizen"])   # Asha asks for Ravi
    assert r.status_code == 403
