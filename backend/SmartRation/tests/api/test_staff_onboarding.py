"""Staff onboarding (migration 0009): applying grants nothing; only an Admin approves, with a reason, audited.

Design: docs/architecture/STAFF_ONBOARDING_DESIGN.md. Synthetic world: shop 1 (owner 50), shop 2 (owner 51),
official 60; this file adds an Admin (70) and a shop without an owner (3).
"""

from __future__ import annotations

import pytest
from ration_world import TEST_PASSWORD, session
from sqlalchemy import select

from app.database.enums import StaffApplicationStatus, UserRole
from app.database.models import AuditLog, RationShop, RefreshToken, StaffApplication, User
from app.security.tokens import TokenUser, create_access_token
from app.utils.time import utc_now

ADMIN_ID = 70


@pytest.fixture
def world(env):
    with session() as db:
        db.add_all([User(Id=ADMIN_ID, FullName="Admin", Email="admin@example.com", MobileNumber="9000000070", PasswordHash="x",
                         Role=int(UserRole.Admin), IsActive=True, CreatedAt=utc_now()),
                    RationShop(Id=3, ShopName="Third FPS", ShopCode="FPS-003", Address="c", District="Nagpur", State="MH",
                               Latitude=0, Longitude=0, IsActive=True, CreatedAt=utc_now())])
        db.commit()
    settings = env["client"].app.state.settings
    token = create_access_token(TokenUser(ADMIN_ID, "admin@example.com", "Admin", "Admin", None), settings)[0]
    return {**env, "admin": {"Authorization": f"Bearer {token}"}}


def _apply(w, headers=None, **fields):
    body = {"requestedRole": "GovernmentOfficial", "office": "Nagpur district office", "designation": "Inspector",
            "proofReference": "EMP-12345", **fields}
    return w["client"].post("/api/staff-applications", headers=headers or w["citizen"], json=body)


def _citizen_id() -> int:
    with session() as db:
        return db.scalar(select(User.Id).where(User.Email == "asha@example.com"))


def _sign_in(w) -> dict:
    r = w["client"].post("/api/auth/login", json={"email": "asha@example.com", "password": TEST_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['data']['accessToken']}"}


def test_applying_grants_nothing(world):
    r = _apply(world)
    assert r.status_code == 200 and r.json()["data"]["status"] == "Pending"
    assert world["client"].get("/api/admin/dashboard", headers=world["citizen"]).status_code == 403
    with session() as db:
        assert db.get(User, _citizen_id()).Role == UserRole.RuralUser
    mine = world["client"].get("/api/staff-applications/mine", headers=world["citizen"]).json()["data"]
    assert [a["requestedRole"] for a in mine] == ["GovernmentOfficial"]


def test_smuggled_fields_are_ignored(world):
    r = _apply(world, status="Approved", userId=60, role="Admin", decidedByUserId=ADMIN_ID)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "Pending" and data["userId"] == _citizen_id()


def test_one_open_application_at_a_time_and_only_citizens_apply(world):
    assert _apply(world).status_code == 200
    r = _apply(world)
    assert r.status_code == 409 and r.json()["errorCode"] == "APPLICATION_PENDING"
    for staff in ("shop", "official", "admin"):
        assert _apply(world, headers=world[staff]).status_code == 403


@pytest.mark.parametrize("fields,status,code", [
    ({"requestedRole": "Admin"}, 400, "INVALID_ROLE"),
    ({"requestedRole": "RuralUser"}, 400, "INVALID_ROLE"),
    ({"requestedRole": "ShopOwner"}, 400, "SHOP_REQUIRED"),
    ({"requestedRole": "ShopOwner", "rationShopId": 999}, 404, None),
    ({"office": " "}, 400, "OFFICE_REQUIRED"),
    ({"proofReference": ""}, 400, None),
])
def test_invalid_applications(world, fields, status, code):
    r = _apply(world, **fields)
    assert r.status_code == status, r.text
    if code:
        assert r.json()["errorCode"] == code


def test_only_an_admin_reviews_and_decides(world):
    app_id = _apply(world).json()["data"]["id"]
    for who in ("citizen", "shop", "official"):
        assert world["client"].get("/api/admin/staff-applications", headers=world[who]).status_code == 403
        r = world["client"].post(f"/api/admin/staff-applications/{app_id}/approve", headers=world[who], json={"reason": "looks fine"})
        assert r.status_code == 403
    queue = world["client"].get("/api/admin/staff-applications", headers=world["admin"]).json()["data"]
    assert [a["id"] for a in queue] == [app_id] and queue[0]["proofReference"] == "EMP-12345"


def test_approval_grants_the_role_ends_sessions_and_is_audited(world):
    citizen_id = _citizen_id()
    app_id = _apply(world).json()["data"]["id"]
    r = world["client"].post(f"/api/admin/staff-applications/{app_id}/approve", headers=world["admin"], json={"reason": ""})
    assert r.status_code == 400                                                       # a reason is required
    r = world["client"].post(f"/api/admin/staff-applications/{app_id}/approve", headers=world["admin"],
                             json={"reason": "Checked employee ID with the district office"})
    assert r.status_code == 200 and r.json()["data"]["status"] == "Approved"
    with session() as db:
        user = db.get(User, citizen_id)
        assert user.Role == UserRole.GovernmentOfficial and user.RationShopId is None
        assert all(t.RevokedAt is not None for t in db.scalars(select(RefreshToken).where(RefreshToken.UserId == citizen_id)))
        audit = db.scalar(select(AuditLog).where(AuditLog.Action == "STAFF_APPROVED"))
        assert audit is not None and "EMP-12345" not in (audit.Details or "")       # never the proof number
    assert world["client"].get("/api/admin/dashboard", headers=_sign_in(world)).status_code == 200
    r = world["client"].post(f"/api/admin/staff-applications/{app_id}/approve", headers=world["admin"], json={"reason": "again please"})
    assert r.status_code == 409 and r.json()["errorCode"] == "NOT_PENDING"


def test_a_shop_owner_application_needs_a_shop_without_an_owner(world):
    taken = _apply(world, requestedRole="ShopOwner", rationShopId=2, office=None).json()["data"]["id"]
    r = world["client"].post(f"/api/admin/staff-applications/{taken}/approve", headers=world["admin"], json={"reason": "licence checked"})
    assert r.status_code == 409 and r.json()["errorCode"] == "SHOP_HAS_OWNER"
    world["client"].post(f"/api/admin/staff-applications/{taken}/reject", headers=world["admin"], json={"reason": "shop already run"})
    free = _apply(world, requestedRole="ShopOwner", rationShopId=3, office=None).json()["data"]["id"]
    r = world["client"].post(f"/api/admin/staff-applications/{free}/approve", headers=world["admin"], json={"reason": "licence checked"})
    assert r.status_code == 200
    with session() as db:
        user = db.get(User, _citizen_id())
        assert (user.Role, user.RationShopId) == (UserRole.ShopOwner, 3)
    headers = _sign_in(world)
    assert world["client"].get("/api/shop/dashboard", headers=headers).status_code == 200
    assert world["client"].get("/api/admin/dashboard", headers=headers).status_code == 403   # shop owner, not official


def test_rejection_keeps_the_role(world):
    app_id = _apply(world).json()["data"]["id"]
    r = world["client"].post(f"/api/admin/staff-applications/{app_id}/reject", headers=world["admin"], json={"reason": "ID not verifiable"})
    assert r.status_code == 200 and r.json()["data"]["status"] == "Rejected"
    with session() as db:
        assert db.get(User, _citizen_id()).Role == UserRole.RuralUser
        assert db.scalar(select(AuditLog.Action).where(AuditLog.Action == "STAFF_REJECTED")) is not None
    assert _apply(world).status_code == 200                                             # may apply again


def test_withdraw_only_my_waiting_application(world):
    app_id = _apply(world).json()["data"]["id"]
    assert world["client"].post(f"/api/staff-applications/{app_id}/withdraw", headers=world["citizen"]).json()["data"]["status"] == "Withdrawn"
    assert world["client"].post(f"/api/staff-applications/{app_id}/withdraw", headers=world["citizen"]).status_code == 409
    r = world["client"].post("/api/auth/register", json={"fullName": "Ravi Kale", "email": "ravi@example.com",
                                                         "mobileNumber": "9000000002", "password": TEST_PASSWORD})
    ravi = {"Authorization": f"Bearer {r.json()['data']['accessToken']}"}
    other = _apply(world).json()["data"]["id"]
    assert world["client"].post(f"/api/staff-applications/{other}/withdraw", headers=ravi).status_code == 404


def test_an_admin_never_decides_their_own_application(world):
    with session() as db:
        a = StaffApplication(UserId=ADMIN_ID, RequestedRole=int(UserRole.GovernmentOfficial), Office="x", Designation="x",
                             ProofReference="xyz", Status=int(StaffApplicationStatus.Pending), CreatedAt=utc_now())
        db.add(a)
        db.commit()
        app_id = a.Id
    r = world["client"].post(f"/api/admin/staff-applications/{app_id}/approve", headers=world["admin"], json={"reason": "self approval"})
    assert r.status_code == 403


def test_revoking_a_staff_role(world):
    app_id = _apply(world).json()["data"]["id"]
    world["client"].post(f"/api/admin/staff-applications/{app_id}/approve", headers=world["admin"], json={"reason": "Checked ID"})
    citizen_id = _citizen_id()
    assert world["client"].post(f"/api/admin/users/{citizen_id}/revoke-staff", headers=world["official"], json={"reason": "no longer"}).status_code == 403
    r = world["client"].post(f"/api/admin/users/{citizen_id}/revoke-staff", headers=world["admin"], json={"reason": "Left the department"})
    assert r.status_code == 200 and r.json()["data"]["previousRole"] == "GovernmentOfficial"
    assert world["client"].get("/api/admin/dashboard", headers=_sign_in(world)).status_code == 403
    assert world["client"].post(f"/api/admin/users/{citizen_id}/revoke-staff", headers=world["admin"], json={"reason": "again"}).status_code == 400
    assert world["client"].post(f"/api/admin/users/{ADMIN_ID}/revoke-staff", headers=world["admin"], json={"reason": "myself"}).status_code == 403
