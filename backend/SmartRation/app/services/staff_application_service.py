"""Staff onboarding: a citizen applies to work as a shop owner or an official; only an Admin decides.

* Applying grants nothing. The request's role, shop and user come from validated fields and the signed-in user; any
  other field in the body is ignored. Only citizens (RuralUser) apply, one open application at a time.
* Approve / reject / revoke are Admin-only, each with a written reason, under row locks (the application, then the
  user), audited. An Admin never decides their own application. Approval and revocation end the person's existing
  sessions (refresh tokens revoked; access tokens are short-lived).
* The proof reference (an ID or licence number the reviewer checked) is shown to Admins and the applicant only and is
  never written to the audit trail or logs. No document images are stored.
Design: docs/architecture/STAFF_ONBOARDING_DESIGN.md. Table: StaffApplications (migration 0009).
"""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound
from app.database.enums import StaffApplicationStatus, UserRole, parse_enum
from app.database.models import RationShop, RefreshToken, StaffApplication, User
from app.services import audit_service
from app.utils.dotnet import dt
from app.utils.time import utc_now

REQUESTABLE = (UserRole.ShopOwner, UserRole.GovernmentOfficial)
LIST_MAX = 200


def _dto(a: StaffApplication, names: dict[int, str], shops: dict[int, str]) -> dict:
    return {
        "id": a.Id, "userId": a.UserId, "applicantName": names.get(a.UserId, ""),
        "requestedRole": UserRole(a.RequestedRole).name, "rationShopId": a.RationShopId,
        "rationShopName": shops.get(a.RationShopId) if a.RationShopId is not None else None,
        "office": a.Office, "designation": a.Designation, "proofReference": a.ProofReference,
        "status": StaffApplicationStatus(a.Status).name, "decisionReason": a.DecisionReason,
        "createdAt": dt(a.CreatedAt), "decidedAt": dt(a.DecidedAt),
    }


def _dtos(db: Session, rows: list[StaffApplication]) -> list[dict]:
    user_ids = {a.UserId for a in rows}
    shop_ids = {a.RationShopId for a in rows if a.RationShopId is not None}
    names = dict(db.execute(select(User.Id, User.FullName).where(User.Id.in_(user_ids))).tuples().all()) if user_ids else {}
    shops = dict(db.execute(select(RationShop.Id, RationShop.ShopName).where(RationShop.Id.in_(shop_ids))).tuples().all()) if shop_ids else {}
    return [_dto(a, names, shops) for a in rows]


def _require_admin(actor: Actor) -> None:
    if actor.role != UserRole.Admin:
        raise Forbidden("Only an administrator can review staff applications.")


def _end_sessions(db: Session, user_id: int) -> None:
    db.execute(update(RefreshToken).where(RefreshToken.UserId == user_id, RefreshToken.RevokedAt.is_(None))
               .values(RevokedAt=utc_now()))


def apply(db: Session, actor: Actor, role_text: str, shop_id: int | None, office: str | None, designation: str,
          proof_reference: str) -> dict:
    if actor.role != UserRole.RuralUser:
        raise Forbidden("Only citizen accounts can apply; your account already has a staff role.")
    role = parse_enum(UserRole, role_text)
    if role not in REQUESTABLE:
        raise BadRequest("RequestedRole must be ShopOwner or GovernmentOfficial.", "INVALID_ROLE")
    if role == UserRole.ShopOwner:
        if shop_id is None:
            raise BadRequest("Choose the ration shop you run.", "SHOP_REQUIRED")
        shop = db.get(RationShop, shop_id)
        if shop is None or not shop.IsActive:
            raise NotFound("Ration shop not found.")
        office = None
    else:
        if not office or len(office.strip()) < 2:
            raise BadRequest("Enter your district or office.", "OFFICE_REQUIRED")
        shop_id = None
    # One open application per person: the user's row is locked while checking and inserting.
    db.scalar(select(User.Id).where(User.Id == actor.user_id).with_for_update())
    open_one = db.scalar(select(StaffApplication.Id).where(StaffApplication.UserId == actor.user_id,
                                                           StaffApplication.Status == int(StaffApplicationStatus.Pending)))
    if open_one is not None:
        raise Conflict("You already have an application waiting for review.", "APPLICATION_PENDING")
    application = StaffApplication(UserId=actor.user_id, RequestedRole=int(role), RationShopId=shop_id,
                                   Office=office.strip() if office else None, Designation=designation.strip(),
                                   ProofReference=proof_reference.strip(), Status=int(StaffApplicationStatus.Pending),
                                   CreatedAt=utc_now())
    db.add(application)
    db.flush()
    audit_service.record(db, actor.user_id, "STAFF_APPLIED", "StaffApplication", str(application.Id),
                         details=role.name, role=actor.role.name, ip_address=actor.ip_address)
    db.commit()
    return _dtos(db, [application])[0]


def mine(db: Session, actor: Actor) -> list[dict]:
    rows = db.scalars(select(StaffApplication).where(StaffApplication.UserId == actor.user_id)
                      .order_by(StaffApplication.CreatedAt.desc(), StaffApplication.Id.desc())).all()
    return _dtos(db, list(rows))


def withdraw(db: Session, actor: Actor, application_id: int) -> dict:
    a = db.scalar(select(StaffApplication).where(StaffApplication.Id == application_id).with_for_update())
    if a is None or a.UserId != actor.user_id:
        raise NotFound("Application not found.")   # someone else's: the same answer as a missing one
    if a.Status != StaffApplicationStatus.Pending:
        raise Conflict("Only a waiting application can be withdrawn.", "NOT_PENDING")
    a.Status = int(StaffApplicationStatus.Withdrawn)
    a.DecidedAt = utc_now()
    audit_service.record(db, actor.user_id, "STAFF_WITHDRAWN", "StaffApplication", str(a.Id), role=actor.role.name,
                         ip_address=actor.ip_address)
    db.commit()
    return _dtos(db, [a])[0]


def list_all(db: Session, actor: Actor, status: str | None, limit: int, offset: int) -> list[dict]:
    _require_admin(actor)
    q = select(StaffApplication)
    if status and status.strip() and status.strip().lower() != "all":
        parsed = parse_enum(StaffApplicationStatus, status.strip())
        if parsed is None:
            raise BadRequest("Unknown application status filter.", "INVALID_STATUS")
        q = q.where(StaffApplication.Status == int(parsed))
    q = q.order_by(StaffApplication.CreatedAt.desc(), StaffApplication.Id.desc()).offset(max(offset, 0)).limit(min(max(limit, 1), LIST_MAX))
    return _dtos(db, list(db.scalars(q).all()))


def _decide(db: Session, actor: Actor, application_id: int, reason: str) -> tuple[StaffApplication, User]:
    _require_admin(actor)
    if not reason or len(reason.strip()) < 5:
        raise BadRequest("Give a reason of at least 5 characters.", "REASON_REQUIRED")
    a = db.scalar(select(StaffApplication).where(StaffApplication.Id == application_id).with_for_update())
    if a is None:
        raise NotFound("Application not found.")
    if a.UserId == actor.user_id:
        raise Forbidden("An administrator cannot decide their own application.")
    if a.Status != StaffApplicationStatus.Pending:
        raise Conflict("This application has already been decided.", "NOT_PENDING")
    user = db.scalar(select(User).where(User.Id == a.UserId).with_for_update())
    if user is None or not user.IsActive:
        raise Conflict("The applicant's account is not active.", "APPLICANT_INACTIVE")
    return a, user


def approve(db: Session, actor: Actor, application_id: int, reason: str) -> dict:
    a, user = _decide(db, actor, application_id, reason)
    if user.Role != UserRole.RuralUser:
        raise Conflict("The applicant already has a staff role.", "ALREADY_STAFF")
    if a.RequestedRole == UserRole.ShopOwner:
        taken = db.scalar(select(func.count()).select_from(User).where(
            User.RationShopId == a.RationShopId, User.Role == int(UserRole.ShopOwner), User.IsActive.is_(True))) or 0
        if taken:
            raise Conflict("This ration shop already has an active owner account.", "SHOP_HAS_OWNER")
    user.Role = a.RequestedRole
    user.RationShopId = a.RationShopId if a.RequestedRole == UserRole.ShopOwner else None
    a.Status = int(StaffApplicationStatus.Approved)
    a.DecidedByUserId, a.DecidedAt, a.DecisionReason = actor.user_id, utc_now(), reason.strip()
    _end_sessions(db, user.Id)
    audit_service.record(db, actor.user_id, "STAFF_APPROVED", "StaffApplication", str(a.Id),
                         details=f"user={user.Id} role={UserRole(a.RequestedRole).name}", role=actor.role.name,
                         ip_address=actor.ip_address)
    db.commit()
    return _dtos(db, [a])[0]


def reject(db: Session, actor: Actor, application_id: int, reason: str) -> dict:
    a, _user = _decide(db, actor, application_id, reason)
    a.Status = int(StaffApplicationStatus.Rejected)
    a.DecidedByUserId, a.DecidedAt, a.DecisionReason = actor.user_id, utc_now(), reason.strip()
    audit_service.record(db, actor.user_id, "STAFF_REJECTED", "StaffApplication", str(a.Id), role=actor.role.name,
                         ip_address=actor.ip_address)
    db.commit()
    return _dtos(db, [a])[0]


def revoke(db: Session, actor: Actor, user_id: int, reason: str) -> dict:
    _require_admin(actor)
    if not reason or len(reason.strip()) < 5:
        raise BadRequest("Give a reason of at least 5 characters.", "REASON_REQUIRED")
    if user_id == actor.user_id:
        raise Forbidden("An administrator cannot revoke their own role.")
    user = db.scalar(select(User).where(User.Id == user_id).with_for_update())
    if user is None:
        raise NotFound("User not found.")
    if user.Role not in (UserRole.ShopOwner, UserRole.GovernmentOfficial):
        raise BadRequest("Only shop owner and official roles can be revoked here.", "NOT_STAFF")
    previous = UserRole(user.Role).name
    user.Role, user.RationShopId = int(UserRole.RuralUser), None
    _end_sessions(db, user.Id)
    audit_service.record(db, actor.user_id, "STAFF_REVOKED", "User", str(user.Id), details=f"from={previous}",
                         role=actor.role.name, ip_address=actor.ip_address)
    db.commit()
    return {"userId": user.Id, "role": UserRole.RuralUser.name, "previousRole": previous}
