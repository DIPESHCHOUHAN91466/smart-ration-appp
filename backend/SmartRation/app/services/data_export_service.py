"""A person's own data, as one JSON document (DPDP Act 2023: the right to a summary of one's personal data).

Every table has an explicit list of the columns that may leave the system, so a column added later is never exported
by accident. Never included: password and token hashes, the two-factor secret, QR references, idempotency keys, and
other people's identities (the staff member who served or resolved something). Aadhaar appears masked only, as stored.
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import IntEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.database.enums import (
    AadhaarVerificationStatus,
    EligibilityStatus,
    FamilyRelationship,
    Gender,
    GrievanceCategory,
    GrievanceStatus,
    MobileVerificationStatus,
    NotificationType,
    PassbookVerificationStatus,
    RationType,
    TokenStatus,
    UserRole,
)
from app.database.models import (
    AadhaarVerification,
    AuditLog,
    Beneficiary,
    Family,
    FamilyMember,
    Grievance,
    MobileVerification,
    Notification,
    PassbookVerification,
    RationCollection,
    Token,
    TokenItem,
    User,
)
from app.utils.time import utc_now

FORMAT_VERSION = 1
AUDIT_ROWS = 5000   # the most recent account events; older ones stay available on request

# table -> (columns that may be exported, {column: enum for a readable name})
FIELDS: dict[type, tuple[tuple[str, ...], dict[str, type[IntEnum]]]] = {
    User: (("Id", "FullName", "Email", "MobileNumber", "Role", "IsActive", "CreatedAt", "TotpEnabledAt"), {"Role": UserRole}),
    Beneficiary: (("BeneficiaryCode", "Address", "Gender", "DateOfBirth", "Village", "District", "State", "Pincode",
                   "IsActive", "IsBlocked", "CreatedAt"), {"Gender": Gender}),
    Family: (("FamilyCode", "RationShopId", "RationSchemeId", "CreatedAt"), {}),
    FamilyMember: (("FullName", "Age", "Gender", "Relationship", "Eligibility"),
                   {"Gender": Gender, "Relationship": FamilyRelationship, "Eligibility": EligibilityStatus}),
    Token: (("TokenNumber", "RationShopId", "Status", "CreatedAt", "CollectedAt"), {"Status": TokenStatus}),
    TokenItem: (("RationType", "Quantity"), {"RationType": RationType}),
    RationCollection: (("CollectionCode", "RationShopId", "VerificationMethod", "CollectedAt"), {}),
    Grievance: (("ReferenceNumber", "RationShopId", "Category", "RationType", "Description", "Status", "Source",
                 "ResolutionNote", "CreatedAt", "UpdatedAt"),
                {"Category": GrievanceCategory, "Status": GrievanceStatus, "RationType": RationType}),
    Notification: (("Type", "Title", "Message", "IsRead", "CreatedAt"), {"Type": NotificationType}),
    AuditLog: (("Action", "Result", "Details", "IpAddress", "CreatedAt"), {}),
    AadhaarVerification: (("AadhaarMasked", "Status", "VerificationDate", "VerificationSource", "VerificationMode"),
                          {"Status": AadhaarVerificationStatus}),
    MobileVerification: (("MobileMasked", "Status", "VerifiedAt", "VerificationSource"), {"Status": MobileVerificationStatus}),
    PassbookVerification: (("PassbookNumber", "Status", "VerificationStatus", "LastUpdated", "VerificationSource"),
                           {"Status": PassbookVerificationStatus}),
}


def _value(value: Any, enum: type[IntEnum] | None) -> Any:
    if enum is not None and isinstance(value, int) and not isinstance(value, bool):
        try:
            return enum(value).name
        except ValueError:
            return value
    if isinstance(value, datetime):
        return value.isoformat() + ("Z" if value.tzinfo is None else "")
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def row(obj: Any) -> dict[str, Any]:
    columns, enums = FIELDS[type(obj)]
    return {column: _value(getattr(obj, column), enums.get(column)) for column in columns}


def export(db: Session, user_id: int) -> dict[str, Any]:
    user = db.get(User, user_id)
    if user is None:
        raise NotFound("Account not found.")
    beneficiary = db.scalar(select(Beneficiary).where(Beneficiary.UserId == user_id).order_by(Beneficiary.Id).limit(1))
    family = db.get(Family, beneficiary.FamilyId) if beneficiary else None
    b_id = beneficiary.Id if beneficiary else -1
    tokens = list(db.scalars(select(Token).where(Token.UserId == user_id).order_by(Token.CreatedAt)))
    bookings = []
    for token in tokens:
        items = db.scalars(select(TokenItem).where(TokenItem.TokenId == token.Id).order_by(TokenItem.Id))
        bookings.append(row(token) | {"items": [row(i) for i in items]})

    def all_of(model, *where, order):
        return [row(r) for r in db.scalars(select(model).where(*where).order_by(order))]

    return {
        "format": "smart-ration-personal-data", "version": FORMAT_VERSION, "exportedAt": _value(utc_now(), None),
        "account": row(user),
        "beneficiary": row(beneficiary) if beneficiary else None,
        "family": (row(family) | {"members": all_of(FamilyMember, FamilyMember.FamilyId == family.Id, order=FamilyMember.Id)})
        if family else None,
        "verifications": {
            "aadhaar": all_of(AadhaarVerification, AadhaarVerification.BeneficiaryId == b_id, order=AadhaarVerification.Id),
            "mobile": all_of(MobileVerification, MobileVerification.BeneficiaryId == b_id, order=MobileVerification.Id),
            "passbook": all_of(PassbookVerification, PassbookVerification.BeneficiaryId == b_id, order=PassbookVerification.Id),
        },
        "bookings": bookings,
        "collections": all_of(RationCollection, RationCollection.BeneficiaryId == b_id, order=RationCollection.CollectedAt),
        "complaints": all_of(Grievance, Grievance.UserId == user_id, order=Grievance.CreatedAt),
        "notifications": all_of(Notification, Notification.UserId == user_id, order=Notification.CreatedAt),
        "accountEvents": [row(a) for a in db.scalars(select(AuditLog).where(AuditLog.UserId == user_id)
                                                     .order_by(AuditLog.CreatedAt.desc()).limit(AUDIT_ROWS))],
    }
