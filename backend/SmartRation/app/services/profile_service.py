"""People and their records: the signed-in user's account, beneficiary profiles (verification, family,
entitlement, collections, the 360° view), families, the dashboard search box and the public badge.

Access rule (one place): a citizen sees only their own beneficiary/family; staff roles see any.
Search is narrower: a shop owner only finds their own shop's beneficiaries and tokens.
The public badge is anonymous by design and returns ONLY non-sensitive fields.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound
from app.database.enums import EligibilityStatus, Gender, TokenStatus, UserRole, VerificationAction, parse_enum
from app.database.models import (
    Beneficiary,
    Family,
    FamilyMember,
    RationCollection,
    RationScheme,
    RationShop,
    TimeSlot,
    Token,
    User,
    VerificationAuditLog,
)
from app.services import ai_rules_service, entitlement_service, verification_audit_service
from app.services._db import require
from app.services.mappers import (
    aadhaar_dto,
    beneficiary_summary,
    collection_history,
    family_dto,
    family_members,
    mobile_dto,
    passbook_dto,
    user_summary,
)
from app.services.verification_service import aadhaar_record, mobile_record, passbook_record
from app.utils.dotnet import enum_name, hhmm, month_year, ymd
from app.utils.masking import mask_mobile
from app.utils.time import utc_now

DOTNET_MIN_DATE = datetime(1, 1, 1)
SEARCH_MAX_PER_TYPE = 5


# ---------------------------------------------------------------- own account and staff user list

def own_profile(db: Session, actor: Actor) -> dict:
    return user_summary(require(db, User, actor.user_id, "User profile not found."))


def update_own_profile(db: Session, actor: Actor, full_name: str, mobile: str) -> dict:
    user = require(db, User, actor.user_id, "User profile not found.")
    mobile = mobile.strip()   # check the value that will be SAVED, so a padded duplicate is a 409, not a 500
    if db.scalar(select(User.Id).where(User.MobileNumber == mobile, User.Id != user.Id).limit(1)):
        raise Conflict("Another account already uses this mobile number.")
    user.FullName = full_name.strip()
    user.MobileNumber = mobile
    db.commit()
    return user_summary(user)


def list_users(db: Session, role: str | None) -> list[dict]:
    q = select(User)
    if role and role.strip():
        parsed = parse_enum(UserRole, role)
        if parsed is None:
            raise BadRequest(f"Unknown role '{role}'.")
        q = q.where(User.Role == int(parsed))
    return [user_summary(u) for u in db.scalars(q.order_by(User.FullName, User.Id))]


# ---------------------------------------------------------------- access rule

def _can_see(db: Session, actor: Actor, owner_user_ids: list[int], family_id: int | None) -> bool:
    """Citizens: only themselves. Officials and admins: everyone. Shop owners: the families registered at their shop,
    and anyone who has booked at their shop (ration portability: a citizen may collect at any shop). Ids are
    sequential, so without this rule one shop account could read every citizen's record (security N2)."""
    if actor.role == UserRole.RuralUser:
        return actor.user_id in owner_user_ids
    if actor.role in (UserRole.GovernmentOfficial, UserRole.Admin):
        return True
    if actor.role != UserRole.ShopOwner or actor.ration_shop_id is None:
        return False   # an unknown role, or a shop account without a shop, sees nobody
    if family_id is not None and db.scalar(select(Family.RationShopId).where(Family.Id == family_id)) == actor.ration_shop_id:
        return True
    return bool(owner_user_ids) and db.scalar(select(Token.Id).where(
        Token.UserId.in_(owner_user_ids), Token.RationShopId == actor.ration_shop_id).limit(1)) is not None


def _load(db: Session, actor: Actor, beneficiary_id: int) -> tuple[Beneficiary, User]:
    beneficiary = db.get(Beneficiary, beneficiary_id)
    if beneficiary is None:
        raise NotFound("Beneficiary not found.")
    if not _can_see(db, actor, [beneficiary.UserId], beneficiary.FamilyId):
        raise Forbidden("You do not have access to this beneficiary.")
    return beneficiary, require(db, User, beneficiary.UserId, "Beneficiary not found.")


def ensure_can_see(db: Session, actor: Actor, beneficiary_id: int) -> None:
    _load(db, actor, beneficiary_id)


def my_beneficiary_id(db: Session, actor: Actor) -> int:
    found = db.scalar(select(Beneficiary.Id).where(Beneficiary.UserId == actor.user_id).order_by(Beneficiary.Id).limit(1))
    if found is None:
        raise NotFound("You do not have a beneficiary profile yet.")
    return found


def _family(db: Session, family_id: int) -> dict:
    family = db.get(Family, family_id)
    return family_dto(family.FamilyCode if family else "", family_members(db, family_id))


# ---------------------------------------------------------------- beneficiary views

def verification(db: Session, actor: Actor, beneficiary_id: int) -> dict:
    beneficiary, user = _load(db, actor, beneficiary_id)
    aadhaar, passbook = aadhaar_record(db, beneficiary.Id), passbook_record(db, beneficiary.Id)
    mobile = mobile_record(db, beneficiary, user)
    db.commit()
    return {"beneficiary": beneficiary_summary(beneficiary, user), "family": _family(db, beneficiary.FamilyId),
            "aadhaarVerification": aadhaar_dto(aadhaar), "passbookVerification": passbook_dto(passbook), "mobileVerification": mobile_dto(mobile)}


def my_verification(db: Session, actor: Actor) -> dict:
    """The citizen's own profile (/beneficiaries/me): `verification` plus the ration shop their family is
    assigned to, which the mobile app shows on the ration card. Staff views are unchanged."""
    data = verification(db, actor, my_beneficiary_id(db, actor))
    beneficiary = db.get(Beneficiary, data["beneficiary"]["id"])
    family = db.get(Family, beneficiary.FamilyId) if beneficiary else None
    shop = db.get(RationShop, family.RationShopId) if family else None
    data["rationShop"] = None if shop is None else {
        "id": shop.Id, "shopName": shop.ShopName, "shopCode": shop.ShopCode,
        "address": shop.Address, "district": shop.District,
    }
    return data


def family(db: Session, actor: Actor, beneficiary_id: int) -> dict:
    beneficiary, _ = _load(db, actor, beneficiary_id)
    return _family(db, beneficiary.FamilyId)


def entitlement(db: Session, actor: Actor, beneficiary_id: int) -> dict:
    beneficiary, _ = _load(db, actor, beneficiary_id)
    return entitlement_service.get_entitlement(db, beneficiary.FamilyId)


def _collections(db: Session, beneficiary_id: int) -> list[RationCollection]:
    return list(db.scalars(select(RationCollection).where(RationCollection.BeneficiaryId == beneficiary_id)
                           .order_by(RationCollection.CollectedAt.desc(), RationCollection.Id.desc())))


def collections(db: Session, actor: Actor, beneficiary_id: int) -> list[dict]:
    _load(db, actor, beneficiary_id)
    return collection_history(db, _collections(db, beneficiary_id))


def full_profile(db: Session, actor: Actor, beneficiary_id: int) -> dict:
    """Beneficiary 360°: everything one screen needs in a single call."""
    beneficiary, user = _load(db, actor, beneficiary_id)
    aadhaar, passbook = aadhaar_record(db, beneficiary.Id), passbook_record(db, beneficiary.Id)
    mobile = mobile_record(db, beneficiary, user)
    db.commit()
    ent = entitlement_service.get_entitlement(db, beneficiary.FamilyId)
    # Fraud-risk signals and the shop's verification/scan logs are for staff. A citizen viewing their own
    # profile must not learn what was flagged about them, so these are not even computed for citizens.
    staff_view = actor.role != UserRole.RuralUser
    insight = ai_rules_service.beneficiary_insight(db, beneficiary.Id) if staff_view else None
    history = _collections(db, beneficiary.Id)

    today = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    upcoming_row = db.execute(
        select(Token, TimeSlot, RationShop.ShopName).join(TimeSlot, TimeSlot.Id == Token.TimeSlotId)
        .join(RationShop, RationShop.Id == Token.RationShopId)
        .where(Token.UserId == beneficiary.UserId, Token.Status == int(TokenStatus.Confirmed), TimeSlot.SlotDate >= today)
        .order_by(TimeSlot.SlotDate, Token.Id).limit(1)).first()
    logs = list(db.scalars(select(VerificationAuditLog).where(VerificationAuditLog.BeneficiaryId == beneficiary.Id)
                           .order_by(VerificationAuditLog.Timestamp.desc(), VerificationAuditLog.Id.desc()).limit(50))) if staff_view else []
    family_row = db.get(Family, beneficiary.FamilyId)
    scheme = db.get(RationScheme, family_row.RationSchemeId) if family_row else None
    fam = _family(db, beneficiary.FamilyId)

    profile = {
        "id": beneficiary.Id, "beneficiaryCode": beneficiary.BeneficiaryCode, "fullName": user.FullName,
        "gender": enum_name(Gender, beneficiary.Gender),
        "dateOfBirth": None if beneficiary.DateOfBirth == DOTNET_MIN_DATE else ymd(beneficiary.DateOfBirth),
        "mobileMasked": mask_mobile(user.MobileNumber), "village": beneficiary.Village, "district": beneficiary.District,
        "state": beneficiary.State, "pincode": beneficiary.Pincode, "profilePhotoUrl": beneficiary.ProfilePhotoUrl,
        "isActive": bool(beneficiary.IsActive), "isBlocked": bool(beneficiary.IsBlocked),
        "registrationDate": ymd(beneficiary.CreatedAt),
        "lastCollectionDate": ymd(history[0].CollectedAt) if history else None,
        "nextCollectionDate": ymd(upcoming_row[1].SlotDate) if upcoming_row else None,
    }
    current_qr = None
    if upcoming_row:
        token, slot, shop_name = upcoming_row
        current_qr = {"tokenId": token.Id, "tokenNumber": token.TokenNumber, "qrCodeValue": token.QRCodeValue,
                      "status": TokenStatus(token.Status).name, "collectionDate": ymd(slot.SlotDate),
                      "bookingTime": hhmm(slot.StartTime), "shopName": shop_name}
    audit = [verification_audit_service.to_dto(x) for x in logs]
    return {
        "profile": profile,
        "family": fam,
        "rationCard": {"rationCardNumber": passbook.PassbookNumber, "status": passbook.Status,
                       "schemeCode": scheme.SchemeCode if scheme else "", "schemeName": scheme.Name if scheme else "",
                       "familySize": fam["familySize"]},
        "aadhaarVerification": aadhaar_dto(aadhaar), "passbookVerification": passbook_dto(passbook), "mobileVerification": mobile_dto(mobile),
        "entitlement": ent,
        "currentQr": current_qr,
        "collectionHistory": collection_history(db, history),
        "verificationHistory": audit,
        "qrScanHistory": [a for a, x in zip(audit, logs, strict=True) if x.Action == VerificationAction.QrScanned],
        "aiInsight": insight,
    }


# ---------------------------------------------------------------- families

def _visible_family(db: Session, actor: Actor, family_id: int) -> Family:
    fam = db.get(Family, family_id)
    if fam is None:
        raise NotFound("Family not found.")
    owners = list(db.scalars(select(Beneficiary.UserId).where(Beneficiary.FamilyId == family_id)))
    if not _can_see(db, actor, owners, family_id):
        raise Forbidden("You do not have access to this family.")
    return fam


def family_by_id(db: Session, actor: Actor, family_id: int) -> dict:
    fam = _visible_family(db, actor, family_id)
    return family_dto(fam.FamilyCode, family_members(db, family_id))


def family_entitlement(db: Session, actor: Actor, family_id: int) -> dict:
    _visible_family(db, actor, family_id)
    return entitlement_service.get_entitlement(db, family_id)


# ---------------------------------------------------------------- search and public badge

def search(db: Session, actor: Actor, q: str | None) -> list[dict]:
    if not q or len(q.strip()) < 2:
        return []
    text = q.strip().lower().replace("!", "!!").replace("%", "!%").replace("_", "!_")
    term = f"%{text}%"   # a literal "contains": % and _ typed by the user are not wildcards

    def like(column):
        return func.lower(column).like(term, escape="!")

    bq = (select(Beneficiary.Id, Beneficiary.BeneficiaryCode, User.FullName).join(User, User.Id == Beneficiary.UserId)
          .join(Family, Family.Id == Beneficiary.FamilyId))
    tq = select(Token.Id, Token.TokenNumber, RationShop.ShopName).join(RationShop, RationShop.Id == Token.RationShopId)
    if actor.role == UserRole.RuralUser:
        bq, tq = bq.where(Beneficiary.UserId == actor.user_id), tq.where(Token.UserId == actor.user_id)
    elif actor.role == UserRole.ShopOwner:
        bq, tq = bq.where(Family.RationShopId == actor.ration_shop_id), tq.where(Token.RationShopId == actor.ration_shop_id)
    elif actor.role not in (UserRole.GovernmentOfficial, UserRole.Admin):
        return []   # an unknown role sees nothing rather than everything
    out = [{"type": "Beneficiary", "title": name, "subtitle": code, "path": f"/beneficiary/{bid}"}
           for bid, code, name in db.execute(bq.where(or_(like(Beneficiary.BeneficiaryCode), like(User.FullName)))
                                             .order_by(Beneficiary.Id).limit(SEARCH_MAX_PER_TYPE))]
    rural = actor.role == UserRole.RuralUser
    out += [{"type": "Token", "title": number, "subtitle": shop, "path": f"/rural/token/{tid}" if rural else "/gov/bookings"}
            for tid, number, shop in db.execute(tq.where(like(Token.TokenNumber)).order_by(Token.Id.desc()).limit(SEARCH_MAX_PER_TYPE))]
    if actor.role in (UserRole.GovernmentOfficial, UserRole.Admin):
        out += [{"type": "Shop", "title": name, "subtitle": code, "path": "/gov/shops"}
                for name, code in db.execute(select(RationShop.ShopName, RationShop.ShopCode)
                                             .where(or_(like(RationShop.ShopName), like(RationShop.ShopCode)))
                                             .order_by(RationShop.Id).limit(SEARCH_MAX_PER_TYPE))]
    return out


def public_badge(db: Session, reference: str) -> dict:
    """Anonymous: never Aadhaar, mobile, address, family members or anything that needs a login."""
    beneficiary = db.scalar(select(Beneficiary).where(Beneficiary.BeneficiaryCode == reference).limit(1))
    if beneficiary is None:
        raise NotFound("No beneficiary found for this reference.")
    fam = require(db, Family, beneficiary.FamilyId, "No beneficiary found for this reference.")
    eligible = db.scalar(select(func.count()).select_from(FamilyMember).where(
        FamilyMember.FamilyId == fam.Id, FamilyMember.Eligibility == int(EligibilityStatus.Eligible))) or 0
    last = db.scalar(select(RationCollection.CollectedAt).where(RationCollection.BeneficiaryId == beneficiary.Id)
                     .order_by(RationCollection.CollectedAt.desc()).limit(1))
    scheme = db.get(RationScheme, fam.RationSchemeId)
    shop = db.get(RationShop, fam.RationShopId)
    return {"beneficiaryCode": beneficiary.BeneficiaryCode, "schemeCode": scheme.SchemeCode if scheme else "",
            "eligibilityBadge": "Eligible" if eligible > 0 else "Not Eligible",
            "verificationBadge": "Verified" if beneficiary.IsActive and not beneficiary.IsBlocked else "Pending",
            "lastCollectionMonth": month_year(last), "shopCode": shop.ShopCode if shop else "",
            "region": f"{beneficiary.District}, {beneficiary.State}"}
