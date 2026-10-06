"""Accounts and beneficiary records: own profile, beneficiary views, families, search, collection history
and the anonymous public badge.

Migrated from the C# UsersController, BeneficiariesController, FamiliesController, SearchController,
PublicController and RationCollectionController (history).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor, actor
from app.api.routes._common import json_body
from app.core.body import Body
from app.core.errors import ok
from app.database.connection import get_db
from app.database.enums import UserRole
from app.security.rate_limit import rate_limit
from app.services import audit_service, data_export_service, profile_service

router = APIRouter(prefix="/api", tags=["people"])
any_user = actor()


@router.get("/users/me/export", summary="Download all my personal data (JSON; DPDP Act 2023)",
            dependencies=[Depends(rate_limit("data-export", lambda s: 5))])
def export_my_data(response: Response, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    data = data_export_service.export(db, who.user_id)
    audit_service.record(db, who.user_id, "DATA_EXPORTED", "User", str(who.user_id), ip_address=who.ip_address)
    db.commit()
    response.headers["Cache-Control"] = "no-store"   # personal data: never kept by a browser or proxy cache
    return ok(data)


@router.get("/users/profile", summary="My account")
def my_profile(who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.own_profile(db, who))


@router.put("/users/profile", summary="Update my name / mobile number (a new number needs currentPassword)",
            dependencies=[Depends(rate_limit("profile-update", lambda s: 10))])
def update_my_profile(body: Body = Depends(json_body), who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    name = body.string("FullName", required=True, max_length=150, min_length=2)
    mobile = body.string("MobileNumber", required=True, max_length=20, is_phone=True)
    password = body.string("CurrentPassword", max_length=100)
    body.raise_if_invalid()
    return ok(profile_service.update_own_profile(db, who, name, mobile, password), "Profile updated")


@router.get("/beneficiaries/me", summary="My beneficiary verification profile")
def my_beneficiary(who: Actor = Depends(actor(UserRole.RuralUser)), db: Session = Depends(get_db)):
    return ok(profile_service.my_verification(db, who))


@router.get("/beneficiaries/{beneficiary_id}/verification", summary="Beneficiary verification profile")
def beneficiary_verification(beneficiary_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.verification(db, who, beneficiary_id))


@router.get("/beneficiaries/{beneficiary_id}/family", summary="Beneficiary's family")
def beneficiary_family(beneficiary_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.family(db, who, beneficiary_id))


@router.get("/beneficiaries/{beneficiary_id}/entitlement", summary="Beneficiary's monthly entitlement")
def beneficiary_entitlement(beneficiary_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.entitlement(db, who, beneficiary_id))


@router.get("/beneficiaries/{beneficiary_id}/collections", summary="Beneficiary's collection history")
def beneficiary_collections(beneficiary_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.collections(db, who, beneficiary_id))


@router.get("/ration/collection/history/{beneficiary_id}", summary="Beneficiary's collection history (alias)")
def collection_history(beneficiary_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.collections(db, who, beneficiary_id))


@router.get("/beneficiaries/{beneficiary_id}/full-profile", summary="Beneficiary 360°: everything one screen needs")
def beneficiary_full_profile(beneficiary_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.full_profile(db, who, beneficiary_id))


@router.get("/families/{family_id}", summary="A family")
def get_family(family_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.family_by_id(db, who, family_id))


@router.get("/families/{family_id}/entitlement", summary="A family's monthly entitlement")
def get_family_entitlement(family_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.family_entitlement(db, who, family_id))


@router.get("/search", summary="Dashboard search (results scoped by role)")
def search(q: str | None = None, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(profile_service.search(db, who, q))


@router.get("/public/beneficiaries/{reference}", summary="Public verification badge (no login; non-sensitive fields only)",
            dependencies=[Depends(rate_limit("public-badge", lambda s: s.public_badge_rate_limit_per_minute))])
def public_badge(reference: str, db: Session = Depends(get_db)):
    return ok(profile_service.public_badge(db, reference))
