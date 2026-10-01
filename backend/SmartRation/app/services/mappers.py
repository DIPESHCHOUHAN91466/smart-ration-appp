"""Database rows -> the JSON objects the frontend reads (field names and formats are the API contract).

Shared by several services so each object has exactly one shape everywhere it appears.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.enums import (
    AadhaarVerificationStatus,
    EligibilityStatus,
    FamilyRelationship,
    Gender,
    MobileVerificationStatus,
    PassbookVerificationStatus,
    RationType,
    TokenStatus,
    UserRole,
)
from app.database.models import (
    AadhaarVerification,
    Beneficiary,
    FamilyMember,
    Inventory,
    MobileVerification,
    PassbookVerification,
    RationCollection,
    RationCollectionItem,
    RationShop,
    TimeSlot,
    Token,
    TokenItem,
    User,
)
from app.utils.dotnet import dt, enum_name, num, timespan, ymd, ymd_hm
from app.utils.masking import mask_mobile

# ---------------------------------------------------------------- tokens (bookings)

def token_dtos(db: Session, tokens: Sequence[Token]) -> list[dict]:
    """Bookings with their user, shop, slot and items, loaded in four queries whatever the count."""
    if not tokens:
        return []
    ids = [t.Id for t in tokens]
    users = {u.Id: u.FullName for u in db.execute(select(User.Id, User.FullName).where(User.Id.in_({t.UserId for t in tokens})))}
    shops = {s.Id: s.ShopName for s in db.execute(select(RationShop.Id, RationShop.ShopName).where(RationShop.Id.in_({t.RationShopId for t in tokens})))}
    slots = {s.Id: s for s in db.scalars(select(TimeSlot).where(TimeSlot.Id.in_({t.TimeSlotId for t in tokens})))}
    items: dict[int, list[dict]] = {}
    for i in db.scalars(select(TokenItem).where(TokenItem.TokenId.in_(ids)).order_by(TokenItem.Id)):
        items.setdefault(i.TokenId, []).append({"rationType": RationType(i.RationType).name, "quantity": num(i.Quantity)})
    out = []
    for t in tokens:
        slot = slots.get(t.TimeSlotId)
        out.append({
            "id": t.Id, "tokenNumber": t.TokenNumber, "status": TokenStatus(t.Status).name,
            "userId": t.UserId, "userName": users.get(t.UserId, ""),
            "rationShopId": t.RationShopId, "rationShopName": shops.get(t.RationShopId, ""),
            "timeSlotId": t.TimeSlotId,
            "slotDate": dt(slot.SlotDate) if slot else "0001-01-01T00:00:00",
            "startTime": timespan(slot.StartTime) if slot else "00:00:00",
            "endTime": timespan(slot.EndTime) if slot else "00:00:00",
            "qrCodeValue": t.QRCodeValue, "items": items.get(t.Id, []),
            "createdAt": dt(t.CreatedAt), "collectedAt": dt(t.CollectedAt),
        })
    return out


def token_dto(db: Session, token: Token) -> dict:
    return token_dtos(db, [token])[0]


# ---------------------------------------------------------------- time slots

def slot_dto(slot: TimeSlot) -> dict:
    remaining = slot.Capacity - slot.BookedCount
    if remaining <= 0:
        status = "Full"
    elif slot.Capacity > 1 and remaining <= max(1, slot.Capacity // 5):
        status = "Limited"
    else:
        status = "Available"
    return {"id": slot.Id, "rationShopId": slot.RationShopId, "slotDate": dt(slot.SlotDate),
            "startTime": timespan(slot.StartTime), "endTime": timespan(slot.EndTime),
            "capacity": slot.Capacity, "bookedCount": slot.BookedCount, "status": status}


# ---------------------------------------------------------------- inventory

def inventory_dto(i: Inventory) -> dict:
    return {"id": i.Id, "rationShopId": i.RationShopId, "rationType": RationType(i.RationType).name,
            "availableQuantity": num(i.AvailableQuantity), "allocatedQuantity": num(i.AllocatedQuantity),
            "minimumStockLevel": num(i.MinimumStockLevel), "isLowStock": i.AvailableQuantity <= i.MinimumStockLevel,
            "updatedAt": dt(i.UpdatedAt)}


# ---------------------------------------------------------------- users

def user_summary(u: User) -> dict:
    return {"id": u.Id, "fullName": u.FullName, "email": u.Email, "mobileNumber": u.MobileNumber,
            "role": UserRole(u.Role).name, "rationShopId": u.RationShopId}


# ---------------------------------------------------------------- beneficiary verification objects

def aadhaar_dto(a: AadhaarVerification) -> dict:
    return {"status": AadhaarVerificationStatus(a.Status).name, "aadhaarMasked": a.AadhaarMasked,
            "verificationDate": ymd(a.VerificationDate), "verificationSource": a.VerificationSource,
            "verificationMode": a.VerificationMode}


def passbook_dto(p: PassbookVerification) -> dict:
    return {"passbookNumber": p.PassbookNumber, "status": p.Status,
            "verificationStatus": PassbookVerificationStatus(p.VerificationStatus).name,
            "lastUpdated": ymd(p.LastUpdated), "verificationSource": p.VerificationSource}


def mobile_dto(m: MobileVerification) -> dict:
    return {"mobileMasked": m.MobileMasked, "status": MobileVerificationStatus(m.Status).name, "verifiedAt": ymd_hm(m.VerifiedAt)}


def beneficiary_summary(b: Beneficiary, user: User) -> dict:
    return {"id": b.Id, "beneficiaryCode": b.BeneficiaryCode, "fullName": user.FullName,
            "mobileMasked": mask_mobile(user.MobileNumber), "address": b.Address,
            "isActive": bool(b.IsActive), "isBlocked": bool(b.IsBlocked)}


def family_dto(family_code: str, members: Sequence[FamilyMember]) -> dict:
    head = next((m for m in members if m.Relationship == FamilyRelationship.Head), None)
    return {
        "familyCode": family_code,
        "familyHeadName": head.FullName if head else "",
        "familySize": len(members),
        "eligibleMemberCount": sum(1 for m in members if m.Eligibility == EligibilityStatus.Eligible),
        "members": [{"id": m.Id, "fullName": m.FullName, "age": m.Age,
                     "relationship": FamilyRelationship(m.Relationship).name,
                     "eligibility": EligibilityStatus(m.Eligibility).name,
                     # "Male" / "Female" / "Other", or null when not recorded.
                     "gender": None if m.Gender is None else enum_name(Gender, m.Gender)} for m in members],
    }


def family_members(db: Session, family_id: int) -> list[FamilyMember]:
    return list(db.scalars(select(FamilyMember).where(FamilyMember.FamilyId == family_id).order_by(FamilyMember.Id)))


# ---------------------------------------------------------------- collections

def collection_history(db: Session, collections: Iterable[RationCollection]) -> list[dict]:
    collections = list(collections)
    if not collections:
        return []
    shops = {s.Id: s.ShopName for s in db.execute(select(RationShop.Id, RationShop.ShopName)
                                                      .where(RationShop.Id.in_({c.RationShopId for c in collections})))}
    items: dict[int, list[dict]] = {}
    for i in db.scalars(select(RationCollectionItem).where(RationCollectionItem.RationCollectionId.in_([c.Id for c in collections]))
                        .order_by(RationCollectionItem.Id)):
        items.setdefault(i.RationCollectionId, []).append({"rationType": RationType(i.RationType).name, "quantity": num(i.Quantity)})
    return [{"collectionCode": c.CollectionCode, "collectedAt": ymd_hm(c.CollectedAt),
             "shopName": shops.get(c.RationShopId, ""), "items": items.get(c.Id, [])} for c in collections]
