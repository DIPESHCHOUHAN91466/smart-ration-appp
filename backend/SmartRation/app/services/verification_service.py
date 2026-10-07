"""Beneficiary verification at the shop counter: after a QR scan or an OTP, is this booking ready for
collection, and if not, exactly why.

Identity records are SYNTHETIC in this system (DATA_MODE=synthetic): the Aadhaar and passbook "checks"
read the stored demo record or create a pre-verified synthetic one — never a real UIDAI or registry call.
Aadhaar is only ever held masked (XXXX-XXXX-1234). Every step is written to the verification audit log.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import ApiError, NotFound
from app.database.enums import (
    AadhaarVerificationStatus,
    Gender,
    MobileVerificationStatus,
    OtpStatus,
    PassbookVerificationStatus,
    TokenStatus,
    VerificationAction,
)
from app.database.models import (
    AadhaarVerification,
    Beneficiary,
    Family,
    MobileVerification,
    OtpVerification,
    PassbookVerification,
    PasswordResetCode,
    RationCollection,
    RationShop,
    TimeSlot,
    Token,
    User,
)
from app.services import entitlement_service, qr_service, verification_audit_service
from app.services._db import require
from app.services.mappers import (
    aadhaar_dto,
    beneficiary_summary,
    collection_history,
    family_dto,
    family_members,
    mobile_dto,
    passbook_dto,
)
from app.utils.dotnet import enum_name, hhmm, midnight
from app.utils.masking import mask_mobile
from app.utils.time import utc_now

SOURCE = "SYNTHETIC_DEMO"
READY, BLOCKED = "READY_FOR_RATION_COLLECTION", "COLLECTION_BLOCKED"


# ---------------------------------------------------------------- synthetic identity records

def aadhaar_record(db: Session, beneficiary_id: int) -> AadhaarVerification:
    record = db.scalar(select(AadhaarVerification).where(AadhaarVerification.BeneficiaryId == beneficiary_id))
    if record is None:
        last_four = (beneficiary_id * 6173) % 9000 + 1000
        record = AadhaarVerification(BeneficiaryId=beneficiary_id, AadhaarReferenceId=f"AAD-DEMO-{beneficiary_id:06d}",
                                     AadhaarMasked=f"XXXX-XXXX-{last_four}", Status=int(AadhaarVerificationStatus.Verified),
                                     VerificationDate=utc_now(), VerificationSource=SOURCE, VerificationMode="PRE_VERIFIED")
        db.add(record)
        db.flush()
    return record


def passbook_record(db: Session, beneficiary_id: int) -> PassbookVerification:
    record = db.scalar(select(PassbookVerification).where(PassbookVerification.BeneficiaryId == beneficiary_id))
    if record is None:
        record = PassbookVerification(BeneficiaryId=beneficiary_id, PassbookNumber=f"PB-DEMO-{beneficiary_id:04d}", Status="ACTIVE",
                                      VerificationStatus=int(PassbookVerificationStatus.Verified), LastUpdated=utc_now(),
                                      VerificationSource=SOURCE)
        db.add(record)
        db.flush()
    return record


def mobile_record(db: Session, beneficiary: Beneficiary, user: User) -> MobileVerification:
    record = db.scalar(select(MobileVerification).where(MobileVerification.BeneficiaryId == beneficiary.Id))
    if record is None:
        record = MobileVerification(BeneficiaryId=beneficiary.Id, MobileMasked=mask_mobile(user.MobileNumber),
                                    Status=int(MobileVerificationStatus.NotVerified), VerificationSource=SOURCE)
        db.add(record)
        db.flush()
    return record


def mobile_number_changed(db: Session, user: User) -> None:
    """The account's mobile number has just changed (user.MobileNumber is the new one). The new number has not been
    shown to work yet, so its verification starts again: NotVerified, with the new masked number. Codes already sent to
    the old number (counter and sign-in codes, password resets) stop working, so they cannot confirm the new number or
    reset the password. The caller commits."""
    for code in db.scalars(select(PasswordResetCode).where(PasswordResetCode.UserId == user.Id,
                                                           PasswordResetCode.Status == int(OtpStatus.Pending))):
        code.Status = int(OtpStatus.Expired)
    beneficiary = db.scalar(select(Beneficiary).where(Beneficiary.UserId == user.Id).limit(1))
    if beneficiary is None:   # staff accounts have no beneficiary record
        return
    for otp in db.scalars(select(OtpVerification).where(OtpVerification.BeneficiaryId == beneficiary.Id,
                                                        OtpVerification.Status == int(OtpStatus.Pending))):
        otp.Status = int(OtpStatus.Expired)
    record = mobile_record(db, beneficiary, user)
    record.MobileMasked = mask_mobile(user.MobileNumber)
    record.Status = int(MobileVerificationStatus.NotVerified)
    record.VerifiedAt = None


def mobile_number_confirmed(db: Session, beneficiary_id: int) -> None:
    """A one-time code sent to the account's current number was entered correctly (at the counter or at sign-in):
    that number works, so it is Verified. The caller commits."""
    beneficiary = db.get(Beneficiary, beneficiary_id)
    user = db.get(User, beneficiary.UserId) if beneficiary is not None else None
    if beneficiary is None or user is None:
        return
    record = mobile_record(db, beneficiary, user)
    if record.Status == MobileVerificationStatus.Verified and record.MobileMasked == mask_mobile(user.MobileNumber):
        return
    record.MobileMasked = mask_mobile(user.MobileNumber)
    record.Status = int(MobileVerificationStatus.Verified)
    record.VerifiedAt = utc_now()


# ---------------------------------------------------------------- the verification bundle

# Gender implied by the relationship itself; anything else (Spouse, Parent, Other) is not guessed.
_RELATIONSHIP_GENDER = {"Son": "Male", "Daughter": "Female"}


def family_with_member_details(family: dict, beneficiary: Beneficiary, aadhaar: AadhaarVerification, entitlement: dict) -> dict:
    """Adds, per member, only what the records actually support (nothing is invented):
      * head of family (the card holder): gender, masked Aadhaar (XXXX-XXXX-1234) and identity status
        from their own verified records; profile photo URL if one is stored;
      * other members: gender only where the relationship implies it (Son / Daughter); Aadhaar, photo and
        identity status are null because FamilyMembers does not record them;
      * every eligible member: their share of the family's monthly entitlement (scheme quota per member).
    """
    eligible_count = entitlement.get("eligibleMemberCount") or 0
    share = [{"rationType": i["rationType"], "quantity": round(i["monthlyEntitlement"] / eligible_count, 3)}
             for i in entitlement.get("items", [])] if eligible_count else []
    head_seen = False
    detailed = []
    for m in family["members"]:
        is_head = m["relationship"] == "Head" and not head_seen
        head_seen = head_seen or is_head
        eligible = m["eligibility"] == "Eligible"
        detailed.append({
            **m,
            "isHead": is_head,
            "gender": enum_name(Gender, beneficiary.Gender) if is_head else _RELATIONSHIP_GENDER.get(m["relationship"]),
            "aadhaarMasked": aadhaar.AadhaarMasked if is_head else None,
            "identityVerified": (aadhaar.Status == AadhaarVerificationStatus.Verified) if is_head else None,
            "photoUrl": beneficiary.ProfilePhotoUrl if is_head else None,
            "monthlyEntitlement": share if eligible else [],
        })
    return {**family, "members": detailed}


def _summary(beneficiary: Beneficiary, token: Token, slot: TimeSlot, aadhaar: AadhaarVerification,
             passbook: PassbookVerification, mobile: MobileVerification, entitlement: dict) -> dict:
    aadhaar_ok = aadhaar.Status == AadhaarVerificationStatus.Verified
    passbook_ok = passbook.VerificationStatus == PassbookVerificationStatus.Verified
    mobile_ok = mobile.Status == MobileVerificationStatus.Verified
    past = midnight(slot.SlotDate) < midnight(utc_now())
    token_valid = token.Status == TokenStatus.Confirmed and not past
    family_eligible = entitlement["eligibleMemberCount"] > 0
    entitlement_available = any(i["todayAllocation"] > 0 for i in entitlement["items"])

    status = TokenStatus(token.Status)
    if beneficiary.IsBlocked:
        reason = "This beneficiary account is blocked."
    elif not beneficiary.IsActive:
        reason = "This beneficiary account is not active."
    elif status == TokenStatus.Completed:
        reason = "This token has already been used for collection."
    elif status == TokenStatus.Cancelled:
        reason = "This booking was cancelled."
    elif past:
        reason = "This token has expired — the booked collection date has passed."
    elif not token_valid:
        reason = f"Token is not valid for collection (status: {status.name})."
    elif aadhaar.Status == AadhaarVerificationStatus.Failed:
        reason = "Aadhaar verification failed."
    elif aadhaar.Status == AadhaarVerificationStatus.Expired:
        reason = "Aadhaar verification has expired."
    elif not aadhaar_ok:
        reason = "Aadhaar verification is pending."
    elif not passbook_ok:
        reason = "Passbook verification is pending."
    elif not mobile_ok:
        reason = "Mobile OTP verification required."
    elif not family_eligible:
        reason = "This beneficiary is not eligible under the selected scheme."
    elif not entitlement_available:
        reason = "No remaining ration entitlement."
    else:
        reason = None
    return {"aadhaarVerified": aadhaar_ok, "passbookVerified": passbook_ok, "mobileVerified": mobile_ok,
            "tokenValid": token_valid, "familyEligible": family_eligible, "entitlementAvailable": entitlement_available,
            "overallStatus": READY if reason is None else BLOCKED, "blockedReason": reason}


def build_response(db: Session, actor: Actor, token: Token, method: str) -> dict:
    beneficiary = db.scalar(select(Beneficiary).where(Beneficiary.UserId == token.UserId).limit(1))
    if beneficiary is None:
        raise NotFound("This user does not have a beneficiary profile yet.")
    user = require(db, User, beneficiary.UserId, "User not found.")
    family = db.get(Family, beneficiary.FamilyId)
    members = family_members(db, beneficiary.FamilyId)
    shop = db.get(RationShop, token.RationShopId)
    slot = require(db, TimeSlot, token.TimeSlotId, "Time slot not found.")

    aadhaar = aadhaar_record(db, beneficiary.Id)
    verification_audit_service.log(db, actor, VerificationAction.AadhaarStatusChecked, "SUCCESS", method,
                                   beneficiary_id=beneficiary.Id, shop_id=token.RationShopId)
    passbook = passbook_record(db, beneficiary.Id)
    verification_audit_service.log(db, actor, VerificationAction.PassbookStatusChecked, "SUCCESS", method,
                                   beneficiary_id=beneficiary.Id, shop_id=token.RationShopId)
    mobile = mobile_record(db, beneficiary, user)
    entitlement = entitlement_service.get_entitlement(db, beneficiary.FamilyId)
    previous = db.scalars(select(RationCollection).where(RationCollection.BeneficiaryId == beneficiary.Id)
                          .order_by(RationCollection.CollectedAt.desc()).limit(10)).all()
    summary = _summary(beneficiary, token, slot, aadhaar, passbook, mobile, entitlement)

    if summary["overallStatus"] == BLOCKED and token.Status == TokenStatus.Completed:
        verification_audit_service.log(db, actor, VerificationAction.TokenAlreadyUsed, "BLOCKED", method, token_number=token.TokenNumber,
                                       beneficiary_id=beneficiary.Id, shop_id=token.RationShopId, reason=summary["blockedReason"])
    verification_audit_service.log(db, actor, VerificationAction.BeneficiaryVerified,
                                   "SUCCESS" if summary["overallStatus"] == READY else "BLOCKED", method,
                                   token_number=token.TokenNumber, beneficiary_id=beneficiary.Id, shop_id=token.RationShopId,
                                   reason=summary["blockedReason"])
    db.commit()
    return {
        "beneficiary": beneficiary_summary(beneficiary, user),
        "family": family_with_member_details(family_dto(family.FamilyCode if family else "", members),
                                             beneficiary, aadhaar, entitlement),
        "aadhaarVerification": aadhaar_dto(aadhaar),
        "passbookVerification": passbook_dto(passbook),
        "mobileVerification": mobile_dto(mobile),
        "booking": {"tokenId": token.Id, "tokenNumber": token.TokenNumber, "status": TokenStatus(token.Status).name,
                    "collectionDate": f"{slot.SlotDate:%Y-%m-%d}", "bookingTime": hhmm(slot.StartTime),
                    "shopId": token.RationShopId, "shopName": shop.ShopName if shop else "", "shopCode": shop.ShopCode if shop else "",
                    "collectionCompleted": token.Status == TokenStatus.Completed},
        "entitlement": entitlement,
        "previousCollections": collection_history(db, previous),
        "verificationSummary": summary,
    }


def verify_by_qr(db: Session, secret: str, actor: Actor, qr_value: str) -> dict:
    try:
        token, parsed = qr_service.resolve_token_for_verification(db, secret, actor, qr_value)
    except ApiError as exc:
        verification_audit_service.log(db, actor, VerificationAction.QrScanned, "FAILED", "QR", reason=exc.message)
        db.commit()
        raise
    # Log the opaque reference, never the raw scanned payload. The beneficiary and shop are recorded too
    # (the C# API left them empty, so the repeated-scan and unusual-shop-activity rules could never fire).
    beneficiary_id = db.scalar(select(Beneficiary.Id).where(Beneficiary.UserId == token.UserId).order_by(Beneficiary.Id).limit(1))
    verification_audit_service.log(db, actor, VerificationAction.QrScanned, "SUCCESS", "QR", reference=parsed.reference,
                                   token_number=token.TokenNumber, beneficiary_id=beneficiary_id, shop_id=token.RationShopId)
    return build_response(db, actor, token, "QR")


def verify_beneficiary_at_shop(db: Session, actor: Actor, beneficiary_id: int, shop_id: int, method: str) -> dict:
    user_id = db.scalar(select(Beneficiary.UserId).where(Beneficiary.Id == beneficiary_id))
    if not user_id:
        raise NotFound("Beneficiary not found.")
    today = midnight(utc_now())
    candidates = db.execute(
        select(Token, TimeSlot.SlotDate).join(TimeSlot, TimeSlot.Id == Token.TimeSlotId)
        .where(Token.UserId == user_id, Token.RationShopId == shop_id, Token.Status == int(TokenStatus.Confirmed))
        .order_by(Token.Id)
    ).all()
    if not candidates:
        raise NotFound("No active booking was found for this beneficiary at your shop.")
    token = min(candidates, key=lambda row: abs((midnight(row[1]) - today).days))[0]   # the booking nearest today
    return build_response(db, actor, token, method)


def response_for_token(db: Session, actor: Actor, token_id: int, method: str) -> dict:
    token = db.get(Token, token_id)
    if token is None:
        raise NotFound("Booking not found.")
    return build_response(db, actor, token, method)
