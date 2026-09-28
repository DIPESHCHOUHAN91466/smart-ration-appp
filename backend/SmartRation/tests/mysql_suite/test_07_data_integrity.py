"""Data integrity: 100 records survive exactly (no truncation, no mojibake, no precision loss),
relationships are enforced, and nothing is orphaned."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.models import AadhaarVerification, Beneficiary, Family, FamilyMember, Inventory, MobileVerification, RationShop, RefreshToken, User
from app.utils.time import utc_now
from mysql_suite.sample_data import people


def fingerprint(db, prefix: str) -> str:
    """SHA-256 over every stored field of the test users, in a stable order."""
    rows = db.execute(select(User.Email, User.FullName, User.MobileNumber, User.IsActive, User.Role, User.CreatedAt)
                      .where(User.Email.like(f"{prefix}.%")).order_by(User.Email)).all()
    return hashlib.sha256(repr(rows).encode()).hexdigest()


def test_100_records_round_trip_exactly(db, make_user):
    group = people("int")
    db.add_all(make_user(p.email, p.mobile, p.full_name) for p in group)
    db.commit()
    db.expire_all()
    stored = {u.Email: u for u in db.scalars(select(User))}
    assert len(stored) == 100
    for p in group:
        u = stored[p.email]
        assert u.FullName == p.full_name, p.index                         # exact characters
        assert len(u.FullName) == len(p.full_name)                        # nothing truncated
    # Byte-level check in MySQL itself: 4-byte emoji and Devanagari stored as real UTF-8.
    emoji = db.execute(text("SELECT HEX(FullName) FROM Users WHERE FullName LIKE :n"), {"n": "%🌾%"}).scalars().first()
    assert "F09F8CBE" in emoji                                             # U+1F33E in UTF-8
    lengths = db.execute(text("SELECT CHAR_LENGTH(FullName), LENGTH(FullName) FROM Users WHERE FullName = :n"),
                         {"n": "अ" * 150}).first()
    assert tuple(lengths) == (150, 450)                                    # 150 characters, 450 bytes


def test_fingerprint_is_stable_across_reads_and_reverted_updates(db, make_user):
    db.add_all(make_user(p.email, p.mobile, p.full_name) for p in people("fp"))
    db.commit()
    before = fingerprint(db, "fp")

    originals = {u.Id: u.FullName for u in db.scalars(select(User))}
    for u in db.scalars(select(User)):
        u.FullName = "temporary"
    db.commit()
    assert fingerprint(db, "fp") != before
    for u in db.scalars(select(User)):
        u.FullName = originals[u.Id]
    db.commit()
    db.expire_all()
    assert fingerprint(db, "fp") == before


def test_decimal_quantities_are_exact(db):
    row = db.scalar(select(Inventory).limit(1))
    original = row.AvailableQuantity
    row.AvailableQuantity = Decimal("0.1") + Decimal("0.2")
    row.AllocatedQuantity = Decimal("12345678901234.123456789012345678901234567890")
    db.commit()
    db.expire_all()
    assert row.AvailableQuantity == Decimal("0.3")                        # not 0.30000000000000004
    assert row.AllocatedQuantity == Decimal("12345678901234.123456789012345678901234567890")
    row.AvailableQuantity, row.AllocatedQuantity = original, Decimal(0)
    db.commit()


def test_datetimes_keep_microseconds(db, make_user):
    moment = datetime(2026, 9, 24, 13, 45, 12, 123456)
    u = make_user("time@example.test", "7500000001")
    u.CreatedAt = moment
    db.add(u)
    db.commit()
    db.expire_all()
    assert db.scalar(select(User.CreatedAt).where(User.Email == "time@example.test")) == moment


def test_foreign_keys_are_enforced(db, make_user):
    shop_id = db.scalar(select(RationShop.Id).limit(1))

    db.add(FamilyMember(FamilyId=999_999, FullName="Ghost", Age=30, Relationship=1, Eligibility=1, DataSource="TEST"))
    with pytest.raises(IntegrityError) as err:
        db.commit()
    assert err.value.orig.args[0] == 1452                                 # parent row missing
    db.rollback()

    family = Family(FamilyCode="FAM-TEST-1", RationShopId=shop_id, RationSchemeId=db.scalar(text("SELECT MIN(Id) FROM RationSchemes")),
                    DataSource="TEST", CreatedAt=utc_now())
    db.add(family)
    db.commit()
    with pytest.raises(IntegrityError) as err:
        db.execute(text("DELETE FROM RationShops WHERE Id = :i"), {"i": shop_id})
    assert err.value.orig.args[0] == 1451                                 # RESTRICT: shop still has families
    db.rollback()
    assert db.scalar(select(func.count()).select_from(RationShop).where(RationShop.Id == shop_id)) == 1


def test_cascade_and_set_null_rules(api, db):
    r = api.post("/api/auth/register", json={"fullName": "Cascade Case", "email": "cascade@example.test",
                                             "mobileNumber": "7500000002", "password": "Valid-Pass-1"})
    assert r.status_code == 200
    user_id = db.scalar(select(User.Id).where(User.Email == "cascade@example.test"))
    assert db.scalar(select(func.count()).select_from(RefreshToken).where(RefreshToken.UserId == user_id)) == 1

    db.execute(text("DELETE FROM Users WHERE Id = :i"), {"i": user_id})   # CASCADE → beneficiary, tokens
    db.commit()
    assert db.scalar(select(func.count()).select_from(RefreshToken).where(RefreshToken.UserId == user_id)) == 0
    assert db.scalar(select(func.count()).select_from(Beneficiary).where(Beneficiary.UserId == user_id)) == 0

    shop = RationShop(ShopName="Temp", ShopCode="TEMP-1", Address="a", District="d", State="s",
                      Latitude=0, Longitude=0, IsActive=True, CreatedAt=utc_now())
    db.add(shop)
    db.flush()
    db.add(User(FullName="Owner", Email="owner@example.test", MobileNumber="7500000003", PasswordHash="x",
                Role=2, IsActive=True, CreatedAt=utc_now(), RationShopId=shop.Id))
    db.commit()
    db.execute(text("DELETE FROM RationShops WHERE Id = :i"), {"i": shop.Id})   # SET NULL on Users
    db.commit()
    assert db.scalar(select(User.RationShopId).where(User.Email == "owner@example.test")) is None


def test_no_orphans_and_no_real_identifiers_after_100_registrations(api, db):
    for p in people("orph"):
        assert api.post("/api/auth/register", json={"fullName": p.full_name, "email": p.email,
                                                    "mobileNumber": p.mobile, "password": p.password}).status_code == 200
    orphans = {
        "users without beneficiary": "SELECT COUNT(*) FROM Users u LEFT JOIN Beneficiaries b ON b.UserId = u.Id WHERE b.Id IS NULL",
        "beneficiaries without family": "SELECT COUNT(*) FROM Beneficiaries b LEFT JOIN Families f ON f.Id = b.FamilyId WHERE f.Id IS NULL",
        "families without members": "SELECT COUNT(*) FROM Families f LEFT JOIN FamilyMembers m ON m.FamilyId = f.Id WHERE m.Id IS NULL",
        "beneficiaries without mobile check": "SELECT COUNT(*) FROM Beneficiaries b LEFT JOIN MobileVerifications m ON m.BeneficiaryId = b.Id WHERE m.Id IS NULL",
    }
    assert {name: db.execute(text(sql)).scalar() for name, sql in orphans.items()} == dict.fromkeys(orphans, 0)

    masked = db.scalars(select(AadhaarVerification.AadhaarMasked)).all()
    assert len(masked) == 100 and all(re.fullmatch(r"XXXX-XXXX-\d{4}", m) for m in masked)
    mobiles = db.scalars(select(MobileVerification.MobileMasked)).all()
    assert all(re.fullmatch(r"\*{6}\d{4}", m) for m in mobiles)
    assert db.scalar(select(func.count(func.distinct(Beneficiary.BeneficiaryCode)))) == 100
