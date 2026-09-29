"""A small synthetic ration world shared by the migrated-route tests (SQLite, test-only values).

Two shops, the DEMO-NFSA scheme (rice 5 kg + wheat 3 kg per eligible member), stock at shop 1, slots for
yesterday / today / tomorrow, a shop owner for each shop, an official, and a citizen registered through the
real /api/auth/register route (so the synthetic beneficiary, family and identity records are provisioned).
`env` is registered as a fixture for every test by conftest.py (pytest_plugins); import the helpers:
    from ration_world import book, qr_payload, session
"""

from __future__ import annotations

from datetime import time, timedelta
from decimal import Decimal

import pytest

from app.database.base import Base
from app.database.connection import get_engine, get_session_factory
from app.database.models import Inventory, RationItem, RationScheme, RationShop, SchemeEntitlementItem, TimeSlot, User
from app.security.tokens import TokenUser, create_access_token
from app.utils.dotnet import midnight
from app.utils.time import utc_now

QR_SECRET = "unit-test-qr-secret-0123456789abcdef"
TEST_PASSWORD = "Unit-Test-Only-9!"   # a test fixture value, never a real password


def session():
    return get_session_factory()()


@pytest.fixture
def env(make_client, request):
    """Parametrize indirectly with {"ai_handler": fn} to fake the AI analytics service."""
    options = getattr(request, "param", None) or {}
    client = make_client(lambda r: None, qr_secret=QR_SECRET, **options)
    settings = client.app.state.settings
    Base.metadata.create_all(get_engine())
    today = midnight(utc_now())
    with session() as db:
        now = utc_now()
        db.add_all([
            RationShop(Id=1, ShopName="Satnavari FPS", ShopCode="FPS-001", Address="a", District="Nagpur", State="MH",
                       Latitude=0, Longitude=0, IsActive=True, CreatedAt=now),
            RationShop(Id=2, ShopName="Other FPS", ShopCode="FPS-002", Address="b", District="Nagpur", State="MH",
                       Latitude=0, Longitude=0, IsActive=True, CreatedAt=now),
            RationScheme(Id=1, SchemeCode="DEMO-NFSA", Name="NFSA", Description="", IsActive=True),
            SchemeEntitlementItem(RationSchemeId=1, RationType=1, QuotaPerEligibleMemberPerMonth=Decimal(5)),
            SchemeEntitlementItem(RationSchemeId=1, RationType=2, QuotaPerEligibleMemberPerMonth=Decimal(3)),
            RationItem(Id=1, RationType=1, Name="Rice", VernacularName="Chawal", Unit="kg", StandardQuotaPerBooking=Decimal(5), IsActive=True),
            RationItem(Id=2, RationType=2, Name="Wheat", VernacularName="Gehu", Unit="kg", StandardQuotaPerBooking=Decimal(3), IsActive=True),
            Inventory(Id=1, RationShopId=1, RationType=1, AvailableQuantity=Decimal(100), AllocatedQuantity=Decimal(0),
                      MinimumStockLevel=Decimal(10), UpdatedAt=now),
            Inventory(Id=2, RationShopId=1, RationType=2, AvailableQuantity=Decimal(50), AllocatedQuantity=Decimal(0),
                      MinimumStockLevel=Decimal(10), UpdatedAt=now),
            User(Id=50, FullName="Shop Owner", Email="shop@example.com", MobileNumber="9000000051", PasswordHash="x", Role=2,
                 IsActive=True, CreatedAt=now, RationShopId=1),
            User(Id=51, FullName="Other Owner", Email="shop2@example.com", MobileNumber="9000000052", PasswordHash="x", Role=2,
                 IsActive=True, CreatedAt=now, RationShopId=2),
            User(Id=60, FullName="Official", Email="gov@example.com", MobileNumber="9000000061", PasswordHash="x", Role=3,
                 IsActive=True, CreatedAt=now),
            TimeSlot(Id=1, RationShopId=1, SlotDate=today, StartTime=time(9), EndTime=time(9, 5), Capacity=2, BookedCount=0),
            TimeSlot(Id=2, RationShopId=1, SlotDate=today + timedelta(days=1), StartTime=time(9), EndTime=time(9, 5), Capacity=1, BookedCount=0),
            TimeSlot(Id=3, RationShopId=1, SlotDate=today - timedelta(days=1), StartTime=time(9), EndTime=time(9, 5), Capacity=2, BookedCount=0),
        ])
        db.commit()

    r = client.post("/api/auth/register", json={"fullName": "Asha Patil", "email": "asha@example.com",
                                                "mobileNumber": "9000000001", "password": TEST_PASSWORD})
    assert r.status_code == 200, r.text
    citizen = r.json()["data"]["accessToken"]

    def bearer(user_id: int, email: str, role: str, shop: int | None) -> dict:
        return {"Authorization": f"Bearer {create_access_token(TokenUser(user_id, email, role, role, shop), settings)[0]}"}

    return {"client": client, "citizen": {"Authorization": f"Bearer {citizen}"},
            "shop": bearer(50, "shop@example.com", "ShopOwner", 1), "other_shop": bearer(51, "shop2@example.com", "ShopOwner", 2),
            "official": bearer(60, "gov@example.com", "GovernmentOfficial", None)}


def book(env, slot_id=1, items=None):
    return env["client"].post("/api/ration/bookings", headers=env["citizen"], json={
        "rationShopId": 1, "timeSlotId": slot_id,
        "items": items or [{"rationType": "Rice", "quantity": 5}, {"rationType": "Wheat", "quantity": 3}]})


def qr_payload(env, token_id):
    r = env["client"].get(f"/api/qr/payload/{token_id}", headers=env["citizen"])
    assert r.status_code == 200
    return r.json()["data"]
