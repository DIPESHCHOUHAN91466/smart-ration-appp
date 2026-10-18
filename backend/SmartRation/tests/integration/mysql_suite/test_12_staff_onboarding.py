"""Staff onboarding on real MySQL, from two application instances (2026-10-18, migration 0009).

The suite's schema is built by the real Alembic migrations, so this also proves 0009 creates StaffApplications with its
CHECK constraints on MySQL. Concurrency: approving the same application many times at once grants the role once and
writes one audit row; one citizen applying many times at once leaves exactly one open application."""

from __future__ import annotations

import time

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.api.dependencies.auth import Actor
from app.core.errors import ApiError
from app.database.enums import StaffApplicationStatus, UserRole
from app.database.models import AuditLog, StaffApplication, User
from app.services import staff_application_service as service
from app.utils.time import utc_now
from mysql_suite.test_10_collection_concurrency import run_parallel
from mysql_suite.test_11_alert_concurrency import two_instances  # noqa: F401  (fixture)

ATTEMPTS = 8


@pytest.fixture
def wide_window(monkeypatch):
    """The service reads the clock between its checks and its writes. Making that read slow widens the race window from
    microseconds to 0.2 s, so a missing lock shows up every run instead of by chance (verified by removing the locks)."""
    real = service.utc_now

    def slow():
        time.sleep(0.2)
        return real()
    monkeypatch.setattr(service, "utc_now", slow)


@pytest.fixture
def people(db, password_hash):
    citizen = User(FullName="Applicant", Email="applicant@example.test", MobileNumber="7000000301", PasswordHash=password_hash,
                   Role=int(UserRole.RuralUser), IsActive=True, CreatedAt=utc_now())
    admin = User(FullName="Admin", Email="admin-onboarding@example.test", MobileNumber="7000000302", PasswordHash=password_hash,
                 Role=int(UserRole.Admin), IsActive=True, CreatedAt=utc_now())
    db.add_all([citizen, admin])
    db.commit()
    return {"citizen": Actor(user_id=citizen.Id, role=UserRole.RuralUser, ration_shop_id=None),
            "admin": Actor(user_id=admin.Id, role=UserRole.Admin, ration_shop_id=None)}


def test_the_database_refuses_an_application_for_any_role_but_shop_owner_or_official(db, people):
    with pytest.raises(DBAPIError):
        db.execute(text("INSERT INTO StaffApplications (UserId, RequestedRole, Designation, ProofReference, Status, CreatedAt) "
                        "VALUES (:u, 4, 'x', 'xyz', 1, NOW())"), {"u": people["citizen"].user_id})
        db.commit()
    db.rollback()


def test_approving_the_same_application_at_once_from_two_instances_grants_once(db, people, two_instances, wide_window):  # noqa: F811
    with two_instances(0) as s:
        app_id = service.apply(s, people["citizen"], "GovernmentOfficial", None, "District office", "Inspector", "EMP-1")["id"]

    def approve(i):
        with two_instances(i) as s:
            return service.approve(s, people["admin"], app_id, "ID checked by the district office")

    results = run_parallel(approve, ATTEMPTS)
    assert [r for r in results if not isinstance(r, (dict, ApiError))] == []          # no deadlock, no 500
    assert len([r for r in results if isinstance(r, dict)]) == 1
    assert {(r.status_code, r.error_code) for r in results if isinstance(r, ApiError)} == {(409, "NOT_PENDING")}
    db.rollback()
    assert db.get(User, people["citizen"].user_id).Role == UserRole.GovernmentOfficial
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.Action == "STAFF_APPROVED")) == 1


def test_one_citizen_applying_many_times_at_once_leaves_one_open_application(db, people, two_instances, wide_window):  # noqa: F811
    def apply(i):
        with two_instances(i) as s:
            return service.apply(s, people["citizen"], "GovernmentOfficial", None, "District office", "Inspector", f"EMP-{i}")

    results = run_parallel(apply, ATTEMPTS)
    assert [r for r in results if not isinstance(r, (dict, ApiError))] == []
    assert len([r for r in results if isinstance(r, dict)]) == 1
    assert {(r.status_code, r.error_code) for r in results if isinstance(r, ApiError)} == {(409, "APPLICATION_PENDING")}
    db.rollback()
    assert db.scalar(select(func.count()).select_from(StaffApplication).where(
        StaffApplication.UserId == people["citizen"].user_id, StaffApplication.Status == int(StaffApplicationStatus.Pending))) == 1
