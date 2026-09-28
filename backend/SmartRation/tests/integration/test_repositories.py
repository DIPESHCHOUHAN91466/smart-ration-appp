"""app.repositories against a real (SQLite) database created from the models."""

from __future__ import annotations

from datetime import datetime, time, timedelta

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401  (register tables)
from app.database.base import Base
from app.models import AuditLog, RationItem, RationScheme, RationShop, RefreshToken, SchemeEntitlementItem, TimeSlot, Token, User
from app.repositories import audit_logs, bookings, catalog, refresh_tokens, users
from app.utils.time import utc_now


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'repo.db').as_posix()}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session
    engine.dispose()


def _user(db: Session, uid: int, email: str, mobile: str) -> User:
    return users.add(db, User(Id=uid, FullName=f"User {uid}", Email=email, MobileNumber=mobile, PasswordHash="x", Role=1, IsActive=True, CreatedAt=utc_now()))


def test_users_lookup_by_email_mobile_and_id(db):
    _user(db, 1, "rural@example.com", "9000000001")
    db.commit()
    assert users.email_taken(db, "rural@example.com") and not users.email_taken(db, "other@example.com")
    assert users.mobile_taken(db, "9000000001") and not users.mobile_taken(db, "9000000009")
    assert users.by_email(db, "rural@example.com").Id == 1
    assert users.by_id(db, 1).Email == "rural@example.com" and users.by_id(db, 99) is None


def test_users_add_flushes_so_the_id_is_available_before_commit(db):
    user = users.add(db, User(FullName="New", Email="new@example.com", MobileNumber="9000000002", PasswordHash="x", Role=1, IsActive=True, CreatedAt=utc_now()))
    assert user.Id is not None
    db.rollback()
    assert not users.email_taken(db, "new@example.com")  # add never commits


def test_injection_shaped_input_is_just_data(db):
    _user(db, 1, "rural@example.com", "9000000001")
    db.commit()
    assert users.by_email(db, "' OR '1'='1") is None
    assert not users.email_taken(db, "rural@example.com' --")
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_refresh_tokens_add_find_and_purge_only_long_expired(db):
    _user(db, 1, "rural@example.com", "9000000001")
    now = utc_now()
    refresh_tokens.add(db, 1, "LIVE", now + timedelta(days=7), now)
    refresh_tokens.add(db, 1, "RECENTLY-EXPIRED", now - timedelta(days=2), now - timedelta(days=9))
    refresh_tokens.add(db, 1, "OLD", now - timedelta(days=40), now - timedelta(days=47))
    db.commit()
    assert refresh_tokens.by_hash(db, "LIVE").UserId == 1 and refresh_tokens.by_hash(db, "missing") is None

    cutoff = now - timedelta(days=30)
    assert refresh_tokens.count_expired_before(db, cutoff) == 1
    assert refresh_tokens.delete_expired_before(db, cutoff) == 1
    db.commit()
    assert sorted(db.scalars(select(RefreshToken.TokenHash)).all()) == ["LIVE", "RECENTLY-EXPIRED"]


def test_audit_log_rows_are_appended_with_every_field(db):
    audit_logs.add(db, user_id=None, action="LOGIN_FAILED", entity_name="User", entity_id=None, details="email=r***@example.com",
                   result="FAILED", role=None, ip_address="127.0.0.1", created_at=utc_now())
    db.commit()
    row = db.scalar(select(AuditLog))
    assert (row.Action, row.Result, row.Details, row.IpAddress) == ("LOGIN_FAILED", "FAILED", "email=r***@example.com", "127.0.0.1")


def test_catalog_returns_only_active_rows_in_a_stable_order(db):
    now = utc_now()
    db.add_all([
        RationShop(Id=1, ShopName="Zeta Shop", ShopCode="S-1", Address="a", District="d", State="s", Latitude=0, Longitude=0, IsActive=True, CreatedAt=now),
        RationShop(Id=2, ShopName="Alpha Shop", ShopCode="S-2", Address="a", District="d", State="s", Latitude=0, Longitude=0, IsActive=True, CreatedAt=now),
        RationShop(Id=3, ShopName="Closed Shop", ShopCode="S-3", Address="a", District="d", State="s", Latitude=0, Longitude=0, IsActive=False, CreatedAt=now),
        RationScheme(Id=1, SchemeCode="DEMO-NFSA", Name="NFSA", Description="", IsActive=True),
        RationScheme(Id=2, SchemeCode="OLD", Name="Old", Description="", IsActive=False),
        RationItem(Id=1, Name="Rice", VernacularName="Chawal", RationType=1, Unit="kg", StandardQuotaPerBooking=5, IsActive=True),
        SchemeEntitlementItem(Id=1, RationSchemeId=1, RationType=1, QuotaPerEligibleMemberPerMonth=5),
    ])
    db.commit()
    assert [s.ShopName for s in catalog.active_shops(db)] == ["Alpha Shop", "Zeta Shop"]
    assert catalog.first_active_shop_id(db) == 1
    assert [s.SchemeCode for s in catalog.active_schemes(db)] == ["DEMO-NFSA"]
    assert catalog.active_scheme_id(db, "DEMO-NFSA") == 1 and catalog.active_scheme_id(db, "OLD") is None
    assert [i.Name for i in catalog.active_items(db)] == ["Rice"]
    assert [q.RationType for q in catalog.scheme_entitlements(db, 1)] == [1]


def test_upcoming_bookings_are_filtered_by_user_status_and_date(db):
    now = utc_now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    db.add(RationShop(Id=1, ShopName="Shop", ShopCode="S-1", Address="a", District="d", State="s", Latitude=0, Longitude=0, IsActive=True, CreatedAt=now))
    _user(db, 1, "a@example.com", "9000000001")
    _user(db, 2, "b@example.com", "9000000002")
    for sid, day in ((1, today + timedelta(days=1)), (2, today - timedelta(days=1))):
        db.add(TimeSlot(Id=sid, RationShopId=1, SlotDate=day, StartTime=time(10), EndTime=time(11), Capacity=10, BookedCount=0))
    rows = [(1, 1, 1, 1), (2, 1, 1, 3), (3, 1, 2, 1), (4, 2, 1, 1)]  # (token id, user, slot, status)
    for tid, uid, sid, status in rows:
        db.add(Token(Id=tid, TokenNumber=f"T-{tid}", UserId=uid, RationShopId=1, TimeSlotId=sid, Status=status, CreatedAt=now))
    db.commit()
    found = bookings.upcoming_for_user(db, 1, today, {1, 2}, limit=5)
    assert [r.TokenNumber for r in found] == ["T-1"]  # not cancelled/collected, not past, not another user's
    assert isinstance(found[0].SlotDate, datetime)
