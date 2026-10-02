"""Citizens' grievances (complaints): file one, see my own, and officials' review. See grievance_service."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies.auth import OFFICIALS, Actor, actor
from app.api.routes._common import idempotency_key, json_body
from app.core.body import Body
from app.core.errors import BadRequest, ok
from app.database.connection import get_db
from app.database.enums import UserRole
from app.security.rate_limit import rate_limit
from app.services import grievance_service

router = APIRouter(prefix="/api", tags=["grievances"])

citizen = actor(UserRole.RuralUser)
officials = actor(*OFFICIALS)
submit_limit = Depends(rate_limit("grievance", lambda s: s.grievance_rate_limit_per_minute))


@router.post("/grievances", summary="File a complaint about my ration shop (returns its reference number)", dependencies=[submit_limit])
def submit(request: Request, body: Body = Depends(json_body), who: Actor = Depends(citizen), db: Session = Depends(get_db)):
    category = body.string("Category", required=True, max_length=40)
    description = body.string("Description", required=True, max_length=grievance_service.DESCRIPTION_MAX)
    ration_type = body.string("RationType", max_length=40)
    source = body.string("Source", max_length=16)
    body.raise_if_invalid()
    key = idempotency_key(request)
    if key and len(key) > 64:
        raise BadRequest("Idempotency-Key must be at most 64 characters.", "INVALID_IDEMPOTENCY_KEY")
    return ok(grievance_service.submit(db, who, category, description, ration_type, source, key), "Complaint registered")


@router.get("/grievances/mine", summary="My complaints, newest first")
def mine(who: Actor = Depends(citizen), db: Session = Depends(get_db)):
    return ok(grievance_service.list_mine(db, who))


@router.get("/grievances", summary="All complaints (officials), optionally one status or shop")
def all_grievances(status: str | None = None, shopId: int | None = None, limit: int = 100,
                   who: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(grievance_service.list_all(db, who, status, shopId, limit))


@router.post("/grievances/{grievance_id}/status", summary="Move a complaint to UnderReview / Resolved / Rejected (officials)")
def update_status(grievance_id: int, body: Body = Depends(json_body), who: Actor = Depends(officials), db: Session = Depends(get_db)):
    status = body.string("Status", required=True, max_length=20)
    note = body.string("Note", max_length=500)
    body.raise_if_invalid()
    return ok(grievance_service.update_status(db, who, grievance_id, status, note), "Complaint updated")
