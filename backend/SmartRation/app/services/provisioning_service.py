"""New-beneficiary provisioning on self-registration.

Port of the C# BeneficiaryProvisioningService + the synthetic Aadhaar/passbook
GetOrCreate services, with identical codes and values. SYNTHETIC DEMO DATA:
no real Aadhaar/passbook registry is called, and the Aadhaar value is a
masked, fabricated reference (XXXX-XXXX-####), never a real number.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BadRequest
from app.core.security import utc_now
from app.db.enums import (
    AadhaarVerificationStatus,
    EligibilityStatus,
    FamilyRelationship,
    Gender,
    MobileVerificationStatus,
    PassbookVerificationStatus,
)
from app.db.models import (
    AadhaarVerification,
    Beneficiary,
    Family,
    FamilyMember,
    MobileVerification,
    PassbookVerification,
    RationScheme,
    RationShop,
    User,
)

SOURCE = "SYNTHETIC_DEMO"
DOTNET_MIN_DATE = datetime(1, 1, 1)  # C# default(DateTime), what the C# API stores for DateOfBirth


def _pending_code() -> str:
    """A unique placeholder until the row has an id and gets its real code (FAM-DEMO-0001, ...).
    Never "": the code columns are UNIQUE, so concurrent registrations inserting the same ""
    would queue on each other's index locks and deadlock (seen as MySQL error 1213)."""
    return f"PENDING-{uuid.uuid4().hex}"


def mask_mobile(mobile: str) -> str:
    return "****" if not mobile or len(mobile) < 4 else "******" + mobile[-4:]


def provision(db: Session, user: User) -> Beneficiary:
    """Family (head = the user) + beneficiary + mobile/Aadhaar/passbook records.
    Flushes to get ids; the caller commits everything in one transaction."""
    shop_id = db.scalar(select(RationShop.Id).where(RationShop.IsActive.is_(True)).order_by(RationShop.Id).limit(1))
    if not shop_id:
        raise BadRequest("No active ration shop is configured to assign this beneficiary to.")
    scheme_id = db.scalar(select(RationScheme.Id).where(RationScheme.SchemeCode == "DEMO-NFSA", RationScheme.IsActive.is_(True)).limit(1))
    if not scheme_id:
        raise BadRequest("No active ration scheme is configured to assign this beneficiary to.")

    now = utc_now()
    family = Family(FamilyCode=_pending_code(), RationShopId=shop_id, RationSchemeId=scheme_id, DataSource=SOURCE, CreatedAt=now)
    db.add(family)
    db.flush()
    family.FamilyCode = f"FAM-DEMO-{family.Id:04d}"

    db.add(FamilyMember(FamilyId=family.Id, FullName=user.FullName, Age=30, Relationship=int(FamilyRelationship.Head),
                        Eligibility=int(EligibilityStatus.Eligible), DataSource=SOURCE))

    beneficiary = Beneficiary(
        BeneficiaryCode=_pending_code(), Address="Demo Village", UserId=user.Id, FamilyId=family.Id, IsActive=True, IsBlocked=False,
        DataSource=SOURCE, CreatedAt=now, Gender=int(Gender.Other), DateOfBirth=DOTNET_MIN_DATE,
        Village="", District="", State="", Pincode="", ProfilePhotoUrl=None,
    )
    db.add(beneficiary)
    db.flush()
    beneficiary.BeneficiaryCode = f"BEN-DEMO-{beneficiary.Id:04d}"

    db.add(MobileVerification(BeneficiaryId=beneficiary.Id, MobileMasked=mask_mobile(user.MobileNumber),
                              Status=int(MobileVerificationStatus.Verified), VerifiedAt=now, VerificationSource=SOURCE))
    db.add(AadhaarVerification(
        BeneficiaryId=beneficiary.Id,
        AadhaarReferenceId=f"AAD-DEMO-{beneficiary.Id:06d}",
        AadhaarMasked=f"XXXX-XXXX-{(beneficiary.Id * 6173) % 9000 + 1000}",
        Status=int(AadhaarVerificationStatus.Verified),
        VerificationDate=now,
        VerificationSource=SOURCE,
        VerificationMode="PRE_VERIFIED",
    ))
    db.add(PassbookVerification(BeneficiaryId=beneficiary.Id, PassbookNumber=f"PB-DEMO-{beneficiary.Id:04d}", Status="ACTIVE",
                                VerificationStatus=int(PassbookVerificationStatus.Verified), LastUpdated=now, VerificationSource=SOURCE))
    db.flush()
    return beneficiary
