"""Functional: create, read, update and delete 100 people, plus edge cases, via the ORM and the HTTP API."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DataError, IntegrityError, OperationalError

from app.models import Beneficiary, User
from mysql_suite.sample_data import long_email, people


def count_users(db) -> int:
    return db.scalar(select(func.count()).select_from(User))


def test_crud_100_people(db, make_user):
    group = people("crud")

    # Create
    db.add_all(make_user(p.email, p.mobile, p.full_name) for p in group)
    db.commit()
    assert count_users(db) == 100

    # Read: every field comes back exactly as written
    for p in group:
        u = db.scalar(select(User).where(User.Email == p.email))
        assert (u.FullName, u.MobileNumber, u.IsActive) == (p.full_name, p.mobile, True)

    # Update: rename everyone, deactivate the even ones
    for u in db.scalars(select(User)).all():
        u.FullName = u.FullName[:140] + " (upd)"
        u.IsActive = int(u.Email.split(".")[1][:3]) % 2 == 1
    db.commit()
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(User).where(User.FullName.like("% (upd)"))) == 100
    assert db.scalar(select(func.count()).select_from(User).where(User.IsActive.is_(False))) == 50

    # Delete: the 50 inactive ones
    for u in db.scalars(select(User).where(User.IsActive.is_(False))).all():
        db.delete(u)
    db.commit()
    assert count_users(db) == 50
    assert db.scalar(select(User).where(User.Email == group[0].email)) is None  # index 0 was even → deleted


def test_register_100_people_through_the_api(api, db):
    group = people("api")
    for p in group:
        r = api.post("/api/auth/register", json={"fullName": p.full_name, "email": p.email, "mobileNumber": p.mobile, "password": p.password})
        assert r.status_code == 200, (p.index, r.json())
        assert r.json()["data"]["user"]["fullName"] == p.full_name.strip()

    assert count_users(db) == 100
    assert db.scalar(select(func.count()).select_from(Beneficiary)) == 100  # each got a beneficiary record

    for p in group[:10]:  # login verifies the stored Argon2 hash; 10 keeps the run short
        r = api.post("/api/auth/login", json={"email": p.email, "password": p.password})
        assert r.status_code == 200
        assert api.post("/api/auth/login", json={"email": p.email, "password": "wrong-password"}).status_code == 401


@pytest.mark.parametrize("field,value,message", [
    ("fullName", "", "The FullName field is required."),
    ("fullName", "   ", "The FullName field is required."),
    ("fullName", "A", "The field FullName must be a string with a minimum length of 2 and a maximum length of 150."),
    ("fullName", "A" * 151, "The field FullName must be a string with a minimum length of 2 and a maximum length of 150."),
    ("email", "", "The Email field is required."),
    ("email", "not-an-email", "The Email field is not a valid e-mail address."),
    ("email", long_email(201), "The field Email must be a string with a maximum length of 200."),
    ("mobileNumber", "abc", "The MobileNumber field is not a valid phone number."),
    ("password", "short", "The field Password must be a string with a minimum length of 8 and a maximum length of 100."),
])
def test_api_rejects_invalid_input_without_touching_the_database(api, db, field, value, message):
    body = {"fullName": "Valid Name", "email": "valid@example.test", "mobileNumber": "7999999999", "password": "Valid-Pass-1"}
    body[field] = value
    r = api.post("/api/auth/register", json=body)
    assert r.status_code == 400
    assert any(e.endswith(": " + message) for e in r.json()["errors"])  # list of "Field: message", as in the C# API
    assert count_users(db) == 0


def test_api_accepts_exact_maximum_lengths(api, db):
    r = api.post("/api/auth/register", json={"fullName": "अ" * 150, "email": long_email(200), "mobileNumber": "7" * 20, "password": "P" * 100})
    assert r.status_code == 200, r.json()
    u = db.scalar(select(User))
    assert (len(u.FullName), len(u.Email), len(u.MobileNumber)) == (150, 200, 20)


def test_duplicate_email_and_mobile_are_rejected(api, db):
    body = {"fullName": "First", "email": "dup@example.test", "mobileNumber": "7000000001", "password": "Valid-Pass-1"}
    assert api.post("/api/auth/register", json=body).status_code == 200
    assert api.post("/api/auth/register", json={**body, "mobileNumber": "7000000002"}).status_code == 409
    assert api.post("/api/auth/register", json={**body, "email": "DUP@example.test", "mobileNumber": "7000000003"}).status_code == 409  # case-insensitive
    assert api.post("/api/auth/register", json={**body, "email": "other@example.test"}).status_code == 409  # same mobile
    assert count_users(db) == 1


def test_database_constraints_back_up_the_api(db, make_user):
    """Even code that skips validation can't store bad data: MySQL itself refuses it."""
    db.add(make_user("a@example.test", "7000000010"))
    db.commit()

    db.add(make_user("a@example.test", "7000000011"))       # duplicate email → unique index
    with pytest.raises(IntegrityError) as err:
        db.commit()
    assert err.value.orig.args[0] == 1062
    db.rollback()

    db.add(make_user(long_email(256), "7000000012"))         # 256 > VARCHAR(255) → error, NOT truncation
    with pytest.raises((DataError, OperationalError)) as err:
        db.commit()
    assert err.value.orig.args[0] == 1406
    db.rollback()

    u = make_user("b@example.test", "7000000013")
    u.FullName = None                                          # NOT NULL
    db.add(u)
    with pytest.raises(IntegrityError) as err:
        db.commit()
    assert err.value.orig.args[0] == 1048
    db.rollback()

    assert count_users(db) == 1


def test_empty_string_is_distinct_from_null(db, make_user):
    db.add(make_user("empty@example.test", "7000000020", full_name=""))
    db.commit()
    assert db.scalar(select(User.FullName).where(User.Email == "empty@example.test")) == ""
