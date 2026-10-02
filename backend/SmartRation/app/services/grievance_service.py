"""Citizens' grievances (complaints): submit with a reference number, follow their status, and officials' review.

* A citizen files a complaint about their own ration shop (taken from their ration card, never from the request)
  and gets a reference number such as GRV-2026-000123 plus a notification. A retry with the same
  Idempotency-Key returns the first complaint instead of filing it twice.
* Descriptions must not contain Aadhaar numbers, OTPs or passwords (the same check the help chat uses).
* Officials and admins see every complaint and move it to UnderReview / Resolved / Rejected; the citizen is
  notified of each change. The description is never written to logs or the audit trail.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.chatbot.intents import contains_sensitive
from app.api.dependencies.auth import Actor
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound
from app.database.enums import GrievanceCategory, GrievanceStatus, NotificationType, RationType, UserRole, parse_enum
from app.database.models import Beneficiary, Family, Grievance, RationShop
from app.services import audit_service, notification_service
from app.utils.dotnet import dt
from app.utils.time import utc_now

SOURCES = ("APP", "ASSISTANT")
DESCRIPTION_MIN, DESCRIPTION_MAX = 10, 1000
REVIEW_STATUSES = (GrievanceStatus.UnderReview, GrievanceStatus.Resolved, GrievanceStatus.Rejected)
STATUS_WORDS = {GrievanceStatus.Submitted: "submitted", GrievanceStatus.UnderReview: "under review",
                GrievanceStatus.Resolved: "resolved", GrievanceStatus.Rejected: "closed without action"}


def _dto(g: Grievance, shop_names: dict[int, str]) -> dict:
    return {
        "id": g.Id, "referenceNumber": g.ReferenceNumber, "category": GrievanceCategory(g.Category).name,
        "rationType": RationType(g.RationType).name if g.RationType is not None else None,
        "description": g.Description, "status": GrievanceStatus(g.Status).name, "source": g.Source,
        "shopId": g.RationShopId, "shopName": shop_names.get(g.RationShopId) if g.RationShopId is not None else None,
        "resolutionNote": g.ResolutionNote, "createdAt": dt(g.CreatedAt), "updatedAt": dt(g.UpdatedAt),
    }


def _dtos(db: Session, rows: list[Grievance]) -> list[dict]:
    ids = {g.RationShopId for g in rows if g.RationShopId is not None}
    names = dict(db.execute(select(RationShop.Id, RationShop.ShopName).where(RationShop.Id.in_(ids))).all()) if ids else {}
    return [_dto(g, names) for g in rows]


def _own_shop(db: Session, user_id: int) -> int | None:
    return db.scalar(select(Family.RationShopId).join(Beneficiary, Beneficiary.FamilyId == Family.Id)
                     .where(Beneficiary.UserId == user_id).order_by(Beneficiary.Id).limit(1))


def submit(db: Session, actor: Actor, category_text: str, description: str, ration_type_text: str | None,
           source: str | None, idempotency_key: str | None) -> dict:
    if actor.role != UserRole.RuralUser:
        raise Forbidden("Only citizens can file a complaint here.")
    if idempotency_key:
        previous = db.scalar(select(Grievance).where(Grievance.IdempotencyKey == idempotency_key))
        if previous is not None:
            if previous.UserId != actor.user_id:
                raise Conflict("This request key was already used.", "IDEMPOTENCY_KEY_REUSED")
            return _dtos(db, [previous])[0]

    category = parse_enum(GrievanceCategory, category_text)
    if category is None:
        raise BadRequest("Choose what the complaint is about.", "INVALID_CATEGORY")
    ration_type = None
    if ration_type_text:
        ration_type = parse_enum(RationType, ration_type_text)
        if ration_type is None:
            raise BadRequest(f"Unknown ration item '{ration_type_text}'.", "INVALID_ITEM")
    text = description.strip()
    if len(text) < DESCRIPTION_MIN:
        raise BadRequest(f"Describe the problem in at least {DESCRIPTION_MIN} characters.", "DESCRIPTION_TOO_SHORT")
    if contains_sensitive(text):
        raise BadRequest("Please remove Aadhaar numbers, OTPs and passwords from the description.", "SENSITIVE_DATA")
    origin = (source or "APP").upper()
    if origin not in SOURCES:
        raise BadRequest("Source must be APP or ASSISTANT.", "INVALID_SOURCE")

    now = utc_now()
    grievance = Grievance(ReferenceNumber=f"PENDING-{uuid.uuid4().hex[:24]}", UserId=actor.user_id,
                          RationShopId=_own_shop(db, actor.user_id), Category=int(category),
                          RationType=int(ration_type) if ration_type is not None else None, Description=text,
                          Status=int(GrievanceStatus.Submitted), Source=origin, IdempotencyKey=idempotency_key or None,
                          CreatedAt=now, UpdatedAt=now)
    try:
        db.add(grievance)
        db.flush()
        grievance.ReferenceNumber = f"GRV-{now.year}-{grievance.Id:06d}"
        notification_service.create(db, actor.user_id, NotificationType.GrievanceUpdate, "Complaint registered",
                                    f"Your complaint {grievance.ReferenceNumber} has been registered. "
                                    "You will be told here when its status changes.")
        audit_service.record(db, actor.user_id, "GRIEVANCE_SUBMITTED", "Grievance", str(grievance.Id),
                             f"{grievance.ReferenceNumber} {category.name} via {origin}",
                             role=actor.role.name, ip_address=actor.ip_address)
        db.commit()
    except IntegrityError:
        # Unique IdempotencyKey: the same request was saved at the same moment by another worker.
        db.rollback()
        raise Conflict("Could not save the complaint due to a concurrent request. Please try again.", "CONCURRENT_UPDATE") from None
    return _dtos(db, [grievance])[0]


def list_mine(db: Session, actor: Actor) -> list[dict]:
    rows = db.scalars(select(Grievance).where(Grievance.UserId == actor.user_id)
                      .order_by(Grievance.CreatedAt.desc(), Grievance.Id.desc())).all()
    return _dtos(db, list(rows))


def list_all(db: Session, actor: Actor, status_text: str | None, shop_id: int | None, limit: int) -> list[dict]:
    if not actor.is_official:
        raise Forbidden("Only government officials can view all complaints.")
    q = select(Grievance)
    if status_text:
        status = parse_enum(GrievanceStatus, status_text)
        if status is None:
            raise BadRequest("Unknown complaint status filter.", "INVALID_STATUS")
        q = q.where(Grievance.Status == int(status))
    if shop_id is not None:
        q = q.where(Grievance.RationShopId == shop_id)
    rows = db.scalars(q.order_by(Grievance.CreatedAt.desc(), Grievance.Id.desc()).limit(max(1, min(limit, 500)))).all()
    return _dtos(db, list(rows))


def update_status(db: Session, actor: Actor, grievance_id: int, status_text: str, note: str | None) -> dict:
    if not actor.is_official:
        raise Forbidden("Only government officials can update complaints.")
    status = parse_enum(GrievanceStatus, status_text)
    if status not in REVIEW_STATUSES:
        raise BadRequest("Status must be UnderReview, Resolved or Rejected.", "INVALID_STATUS")
    grievance = db.get(Grievance, grievance_id)
    if grievance is None:
        raise NotFound("Complaint not found.")
    clean_note = note.strip() if note and note.strip() else None
    if clean_note and contains_sensitive(clean_note):
        raise BadRequest("Please remove Aadhaar numbers, OTPs and passwords from the note.", "SENSITIVE_DATA")
    grievance.Status = int(status)
    grievance.ResolutionNote = clean_note
    grievance.ResolvedByUserId = actor.user_id
    grievance.UpdatedAt = utc_now()
    message = f"Your complaint {grievance.ReferenceNumber} is now {STATUS_WORDS[status]}."
    if clean_note:
        message += f" Note: {clean_note}"
    notification_service.create(db, grievance.UserId, NotificationType.GrievanceUpdate, "Complaint update", message)
    audit_service.record(db, actor.user_id, f"GRIEVANCE_{status.name.upper()}", "Grievance", str(grievance.Id),
                         grievance.ReferenceNumber, role=actor.role.name, ip_address=actor.ip_address)
    db.commit()
    return _dtos(db, [grievance])[0]
