"""Seed SYNTHETIC reference and demo data. Idempotent and non-destructive.

Reference data (ration items, 10 demo shops, the two demo schemes and their entitlements,
inventory tiers, 5-minute slot rules) is read from data/synthetic/reference/*.json — the same
values as the C# DbInitializer. Each group is inserted only when its
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

import json
import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path

from _common import database_url, engine, safe_url
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, utc_now
from app.db.enums import RationType, UserRole
from app.db.models import Inventory, RationItem, RationScheme, RationShop, SchemeEntitlementItem, TimeSlot, User

# The synthetic reference data lives in <repo>/data/synthetic/reference/*.json (clearly labelled
# isSynthetic / SYNTHETIC_DEMO). SYNTHETIC_DATA_DIR overrides the location (e.g. in Docker).
DATA_DIR = Path(os.environ.get("SYNTHETIC_DATA_DIR") or Path(__file__).resolve().parents[3] / "data" / "synthetic" / "reference")


def _records(name: str):
    document = json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))
    if not document.get("_meta", {}).get("isSynthetic"):
        raise SystemExit(f"{name}.json is not marked as synthetic data; refusing to seed it.")
    return document["records"]


_rules = _records("inventory_rules")
SLOT_CAPACITY = _rules["slotCapacity"]
# Past days give collection history something to attach to (same range as the C# DbInitializer: -5..+2).
SLOT_DAYS = range(-_rules.get("slotDaysBack", 0), _rules["slotDaysAhead"] + 1)
ITEMS = [(RationType[r["rationType"]], r["name"], r["vernacularName"], r["unit"], r["standardQuotaPerBooking"]) for r in _records("ration_items")]
SHOPS = [(s["shopName"], s["shopCode"], s["address"], s["taluka"], s["village"], s["latitude"], s["longitude"]) for s in _records("shops")]
SCHEMES = [(s["schemeCode"], s["name"], s["description"], [s["quotaPerEligibleMemberPerMonth"][t.name] for t in RationType])
           for s in _records("schemes")]
MINIMUM_STOCK = [_rules["minimumStockLevel"][t.name] for t in RationType]  # per RationType 1..6


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
                       for t, q in zip(RationType, quotas, strict=True))
        done.append(f"{len(SCHEMES)} schemes with entitlements")

    if _is_empty(db, Inventory):
        for i, shop in enumerate(shops):
            tier = i % 4
            factor = 0.3 if tier == 0 else 0.8 if tier == 1 else 3.0 + i * 0.15
            db.add_all(Inventory(RationShopId=shop.Id, RationType=int(t), AvailableQuantity=_round_half_even(m * factor),
                                 AllocatedQuantity=0, MinimumStockLevel=m, UpdatedAt=now)
                       for t, m in zip(RationType, MINIMUM_STOCK, strict=True))
        done.append(f"inventory for {len(shops)} shops")

    if _is_empty(db, TimeSlot):
        today = datetime(now.year, now.month, now.day)
        for shop in shops:
            for offset in SLOT_DAYS:
                for minutes in range(9 * 60, 17 * 60, 5):
                    db.add(TimeSlot(RationShopId=shop.Id, SlotDate=today + timedelta(days=offset),
                                    StartTime=time(minutes // 60, minutes % 60),
                                    EndTime=time((minutes + 5) // 60, (minutes + 5) % 60),
                                    Capacity=SLOT_CAPACITY, BookedCount=0))
        done.append(f"time slots for {len(SLOT_DAYS)} days ({SLOT_DAYS.start:+d} to {SLOT_DAYS.stop - 1:+d})")

    if _is_empty(db, User):
        demo_password = os.environ.get("SEED_DEMO_PASSWORD")
        admin_email, admin_password = os.environ.get("SEED_ADMIN_EMAIL"), os.environ.get("SEED_ADMIN_PASSWORD")
        satnavari = next((s.Id for s in shops if s.ShopCode == "SR-SATNAVARI-001"), None)
        if demo_password:
            h = hash_password(demo_password)
            db.add_all([
                User(FullName="Rahul Patil", Email="rural@example.com", MobileNumber="9000000001", PasswordHash=h,
                     Role=int(UserRole.RuralUser), IsActive=True, CreatedAt=now),
                User(FullName="Satnavari Shop Owner", Email="shop@example.com", MobileNumber="9000000051", PasswordHash=h,
                     Role=int(UserRole.ShopOwner), RationShopId=satnavari, IsActive=True, CreatedAt=now),
                User(FullName="District Government Officer", Email="officer@example.com", MobileNumber="9000000052",
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
    from app.core.config import get_settings

    if get_settings().data_mode != "synthetic":
        # Synthetic demo records must never be written into a real-data database.
        print("Refusing: DATA_MODE is not 'synthetic'; synthetic seed data can't be loaded.")
        return 1
    print(f"Database: {safe_url(database_url())}")
    eng = engine()
    with Session(eng) as db, db.begin():  # one transaction: all or nothing
        done = seed(db)
    eng.dispose()
    print("Seeded: " + ", ".join(done) if done else "Nothing to seed; every reference table already has data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
