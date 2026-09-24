"""Seed SYNTHETIC reference and demo data. Idempotent and non-destructive.

Port of the reference part of the C# DbInitializer, with identical values:
ration items, 10 demo shops, the two demo schemes and their entitlements,
inventory tiers and 5-minute time slots. Each group is inserted only when its
table is empty, so running this against an existing database changes nothing.

Users (only when the Users table is empty):
  * demo users rural@/shop@/officer@example.com  - password from SEED_DEMO_PASSWORD
  * an admin                                      - SEED_ADMIN_EMAIL + SEED_ADMIN_PASSWORD
Passwords are never stored in source; if the variables are unset, no users are created.
All data is fabricated; no real Aadhaar, passbook or personal data is used.

Usage (from backend/SmartRation.Python):
    .venv\\Scripts\\python scripts\\seed_database.py
"""

from __future__ import annotations

import math
import os
import sys
from datetime import datetime, time, timedelta

from _common import engine, safe_url, database_url
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, utc_now
from app.db.enums import RationType, UserRole
from app.db.models import Inventory, RationItem, RationScheme, RationShop, SchemeEntitlementItem, TimeSlot, User

SLOT_CAPACITY = 2

ITEMS = [
    (RationType.Rice, "Rice", "Tandul", "kg", 5),
    (RationType.Wheat, "Wheat", "Gahu", "kg", 5),
    (RationType.Sugar, "Sugar", "Sakhar", "kg", 1),
    (RationType.Pulses, "Pulses", "Daal", "kg", 2),
    (RationType.EdibleOil, "Edible Oil", "Tel", "L", 1),
    (RationType.Salt, "Salt", "Mith", "kg", 1),
]

# (name, code, address, taluka, village, lat, lng)
SHOPS = [
    ("Satnavari Ration Shop", "SR-SATNAVARI-001", "Main Road, Satnavari", "Nagpur Rural", "Satnavari", 21.1904, 79.0850),
    ("Koradi Ration Shop", "SR-KORADI-001", "Station Road, Koradi", "Kamptee", "Koradi", 21.2472, 79.1197),
] + [
    (name, f"SHOP-DEMO-{i:03d}", f"Main Road, {village}", taluka, village, lat, lng)
    for i, (name, taluka, village, lat, lng) in enumerate([
        ("Hingna Ration Shop", "Hingna", "Hingna", 21.0947, 79.0177),
        ("Kamptee Ration Shop", "Kamptee", "Kamptee", 21.2185, 79.1927),
        ("Wadi Ration Shop", "Nagpur Rural", "Wadi", 21.2016, 78.9814),
        ("Mouda Ration Shop", "Mouda", "Mouda", 21.3799, 79.3524),
        ("Ramtek Ration Shop", "Ramtek", "Ramtek", 21.3959, 79.3306),
        ("Katol Ration Shop", "Katol", "Katol", 21.2667, 78.5833),
        ("Umred Ration Shop", "Umred", "Umred", 20.8500, 79.3333),
        ("Saoner Ration Shop", "Saoner", "Saoner", 21.3833, 78.9167),
    ], start=1)
]

SCHEMES = [
    ("DEMO-NFSA", "Demo National Food Security Scheme",
     "Synthetic demo scheme modeled loosely on NFSA-style entitlements. Not a real government scheme.",
     [5, 3, 1, 1, 0.5, 0.25]),
    ("DEMO-AAY", "Demo Priority Household Scheme",
     "Synthetic demo scheme with a higher flat entitlement, modeled loosely on Antyodaya-style schemes. Not a real government scheme.",
     [7, 4, 1.5, 1.5, 1, 0.5]),
]

MINIMUM_STOCK = [300, 300, 200, 150, 100, 80]  # per RationType 1..6


def _round_half_even(value: float) -> int:
    # C# Math.Round(decimal, 0) is banker's rounding; Python's round() matches.
    return round(value)


def _is_empty(db: Session, model) -> bool:
    return not db.scalar(select(func.count()).select_from(model))


def seed(db: Session) -> list[str]:
    done: list[str] = []
    now = utc_now()

    if _is_empty(db, RationItem):
        db.add_all(RationItem(RationType=int(t), Name=n, VernacularName=v, Unit=u, StandardQuotaPerBooking=q, IsActive=True)
                   for t, n, v, u, q in ITEMS)
        done.append(f"{len(ITEMS)} ration items")

    if _is_empty(db, RationShop):
        db.add_all(RationShop(ShopName=n, ShopCode=c, Address=a, District="Nagpur", State="Maharashtra", Taluka=t,
                              Village=v, Latitude=lat, Longitude=lng, IsActive=True, CreatedAt=now)
                   for n, c, a, t, v, lat, lng in SHOPS)
        done.append(f"{len(SHOPS)} ration shops")
    db.flush()
    shops = db.scalars(select(RationShop).order_by(RationShop.Id)).all()

    if _is_empty(db, RationScheme):
        for code, name, desc, quotas in SCHEMES:
            scheme = RationScheme(SchemeCode=code, Name=name, Description=desc, IsActive=True)
            db.add(scheme)
            db.flush()
            db.add_all(SchemeEntitlementItem(RationSchemeId=scheme.Id, RationType=int(t), QuotaPerEligibleMemberPerMonth=q)
                       for t, q in zip(RationType, quotas))
        done.append(f"{len(SCHEMES)} schemes with entitlements")

    if _is_empty(db, Inventory):
        for i, shop in enumerate(shops):
            tier = i % 4
            factor = 0.3 if tier == 0 else 0.8 if tier == 1 else 3.0 + i * 0.15
            db.add_all(Inventory(RationShopId=shop.Id, RationType=int(t), AvailableQuantity=_round_half_even(m * factor),
                                 AllocatedQuantity=0, MinimumStockLevel=m, UpdatedAt=now)
                       for t, m in zip(RationType, MINIMUM_STOCK))
        done.append(f"inventory for {len(shops)} shops")

    if _is_empty(db, TimeSlot):
        today = datetime(now.year, now.month, now.day)
        for shop in shops:
            for offset in range(0, 3):
                for minutes in range(9 * 60, 17 * 60, 5):
                    db.add(TimeSlot(RationShopId=shop.Id, SlotDate=today + timedelta(days=offset),
                                    StartTime=time(minutes // 60, minutes % 60),
                                    EndTime=time((minutes + 5) // 60, (minutes + 5) % 60),
                                    Capacity=SLOT_CAPACITY, BookedCount=0))
        done.append("time slots for today and the next 2 days")

    if _is_empty(db, User):
        demo_password = os.environ.get("SEED_DEMO_PASSWORD")
        admin_email, admin_password = os.environ.get("SEED_ADMIN_EMAIL"), os.environ.get("SEED_ADMIN_PASSWORD")
        satnavari = next((s.Id for s in shops if s.ShopCode == "SR-SATNAVARI-001"), None)
        if demo_password:
            h = hash_password(demo_password)
            db.add_all([
                User(FullName="Rahul Patil", Email="rural@example.com", MobileNumber="9876543210", PasswordHash=h,
                     Role=int(UserRole.RuralUser), IsActive=True, CreatedAt=now),
                User(FullName="Satnavari Shop Owner", Email="shop@example.com", MobileNumber="9876543211", PasswordHash=h,
                     Role=int(UserRole.ShopOwner), RationShopId=satnavari, IsActive=True, CreatedAt=now),
                User(FullName="District Government Officer", Email="officer@example.com", MobileNumber="9876543212",
                     PasswordHash=h, Role=int(UserRole.GovernmentOfficial), IsActive=True, CreatedAt=now),
            ])
            done.append("3 demo users")
        if admin_email and admin_password:
            if len(admin_password) < 12:
                raise SystemExit("SEED_ADMIN_PASSWORD must be at least 12 characters.")
            db.add(User(FullName="System Administrator", Email=admin_email.strip().lower(), MobileNumber="9000000000",
                        PasswordHash=hash_password(admin_password), Role=int(UserRole.Admin), IsActive=True, CreatedAt=now))
            done.append(f"admin {admin_email}")
        if not demo_password and not (admin_email and admin_password):
            print("NOTE: no users created (set SEED_DEMO_PASSWORD and/or SEED_ADMIN_EMAIL + SEED_ADMIN_PASSWORD).")
    return done


def main() -> int:
    print(f"Database: {safe_url(database_url())}")
    eng = engine()
    with Session(eng) as db, db.begin():  # one transaction: all or nothing
        done = seed(db)
    eng.dispose()
    print("Seeded: " + ", ".join(done) if done else "Nothing to seed; every reference table already has data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
