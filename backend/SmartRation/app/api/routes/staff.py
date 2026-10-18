"""Staff onboarding: apply to work as a shop owner or official (citizens); review and decide (Admin only).
See staff_application_service and docs/architecture/STAFF_ONBOARDING_DESIGN.md."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor, actor
from app.api.routes._common import json_body
from app.core.body import Body
from app.core.errors import ok
from app.database.connection import get_db
from app.database.enums import UserRole
from app.security.rate_limit import rate_limit
from app.services import staff_application_service as service

router = APIRouter(prefix="/api", tags=["staff onboarding"])

citizen = actor(UserRole.RuralUser)
admin = actor(UserRole.Admin)
apply_limit = Depends(rate_limit("staff-application", lambda s: s.staff_application_rate_limit_per_minute))


@router.post("/staff-applications", summary="Apply to work as a shop owner or an official (grants nothing until an Admin approves)",
             dependencies=[apply_limit])
def apply(body: Body = Depends(json_body), who: Actor = Depends(citizen), db: Session = Depends(get_db)):
    role = body.string("RequestedRole", required=True, max_length=40)
    shop_id = body.integer("RationShopId")
    office = body.string("Office", max_length=200)
    designation = body.string("Designation", required=True, max_length=120, min_length=2)
    proof = body.string("ProofReference", required=True, max_length=120, min_length=3)
    body.raise_if_invalid()
    return ok(service.apply(db, who, role, shop_id, office, designation, proof), "Application received")


@router.get("/staff-applications/mine", summary="My staff applications, newest first")
def mine(who: Actor = Depends(citizen), db: Session = Depends(get_db)):
    return ok(service.mine(db, who))


@router.post("/staff-applications/{application_id}/withdraw", summary="Withdraw my waiting application")
def withdraw(application_id: int, who: Actor = Depends(citizen), db: Session = Depends(get_db)):
    return ok(service.withdraw(db, who, application_id), "Application withdrawn")


@router.get("/admin/staff-applications", summary="Staff applications to review (Admin), newest first")
def review_queue(status: str | None = "Pending", limit: int = 100, offset: int = 0, who: Actor = Depends(admin),
                 db: Session = Depends(get_db)):
    return ok(service.list_all(db, who, status, limit, offset))


def _reason(body: Body) -> str:
    reason = body.string("Reason", required=True, max_length=500)
    body.raise_if_invalid()
    return reason or ""


@router.post("/admin/staff-applications/{application_id}/approve", summary="Approve: grant the requested role (Admin)")
def approve(application_id: int, body: Body = Depends(json_body), who: Actor = Depends(admin), db: Session = Depends(get_db)):
    return ok(service.approve(db, who, application_id, _reason(body)), "Application approved")


@router.post("/admin/staff-applications/{application_id}/reject", summary="Reject: the role stays citizen (Admin)")
def reject(application_id: int, body: Body = Depends(json_body), who: Actor = Depends(admin), db: Session = Depends(get_db)):
    return ok(service.reject(db, who, application_id, _reason(body)), "Application rejected")


@router.post("/admin/users/{user_id}/revoke-staff", summary="Return a shop owner or official to a citizen account (Admin)")
def revoke_staff(user_id: int, body: Body = Depends(json_body), who: Actor = Depends(admin), db: Session = Depends(get_db)):
    return ok(service.revoke(db, who, user_id, _reason(body)), "Staff role revoked")
