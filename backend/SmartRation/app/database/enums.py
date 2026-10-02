"""Enums stored as integers in the database.

`.name` is the exact string the API returns in JSON (e.g. "ShopOwner", "Confirmed"); the numbers are
what the tables store. Never renumber a member: existing rows and the AI service (ai/domain.py) and the
frontend (src/types/api.js) depend on them — tests/regression checks they stay in step.
"""

from enum import IntEnum


class UserRole(IntEnum):
    RuralUser = 1
    ShopOwner = 2
    GovernmentOfficial = 3
    Admin = 4


class FamilyRelationship(IntEnum):
    Head = 1
    Spouse = 2
    Son = 3
    Daughter = 4
    Parent = 5
    Other = 6


class EligibilityStatus(IntEnum):
    Eligible = 1
    NotEligible = 2
    Pending = 3
    VerificationRequired = 4


class Gender(IntEnum):
    Male = 1
    Female = 2
    Other = 3


class AadhaarVerificationStatus(IntEnum):
    NotVerified = 1
    Pending = 2
    Verified = 3
    Failed = 4
    Expired = 5


class PassbookVerificationStatus(IntEnum):
    NotVerified = 1
    Pending = 2
    Verified = 3
    Failed = 4


class MobileVerificationStatus(IntEnum):
    NotVerified = 1
    Pending = 2
    Verified = 3
    Failed = 4


class RationType(IntEnum):
    Rice = 1
    Wheat = 2
    Sugar = 3
    Pulses = 4
    EdibleOil = 5
    Salt = 6


class TokenStatus(IntEnum):
    Pending = 1
    Confirmed = 2
    Completed = 3
    Cancelled = 4
    NoShow = 5


class InventoryMovementType(IntEnum):
    Received = 1       # stock delivered to the shop (e.g. against a challan)
    Distributed = 2    # issued to a beneficiary through a collection
    Damaged = 3        # spoiled / damaged / written off
    Adjustment = 4     # manual correction; Quantity may be negative


class NotificationType(IntEnum):
    BookingConfirmed = 1
    TokenGenerated = 2
    SlotReminder = 3
    CollectionCompleted = 4
    BookingCancelled = 5
    LowInventory = 6
    VerificationResult = 7
    AIAlert = 8
    SystemAnnouncement = 9
    GrievanceUpdate = 10


class GrievanceCategory(IntEnum):
    """What a citizen's complaint is about."""
    LessRation = 1           # received less than entitled / booked
    PoorQuality = 2          # spoiled, mixed or bad-quality grain
    ShopClosed = 3           # shop closed during its hours / slot
    Overcharged = 4          # asked to pay more than allowed
    TokenProblem = 5         # booking / token / QR did not work
    VerificationProblem = 6  # Aadhaar / OTP / identity check failed
    StaffBehaviour = 7       # rude or unfair treatment
    Other = 8


class GrievanceStatus(IntEnum):
    Submitted = 1
    UnderReview = 2
    Resolved = 3
    Rejected = 4


class OtpStatus(IntEnum):
    Pending = 1
    Verified = 2
    Expired = 3
    Failed = 4


class VerificationAction(IntEnum):
    QrScanned = 1
    BeneficiaryVerified = 2
    AadhaarStatusChecked = 3
    PassbookStatusChecked = 4
    OtpRequested = 5
    OtpVerified = 6
    OtpFailed = 7
    CollectionConfirmed = 8
    CollectionRejected = 9
    TokenAlreadyUsed = 10


class AIAlertSeverity(IntEnum):
    Info = 0
    Low = 1
    Medium = 2
    High = 3
    Critical = 4


class AIAlertStatus(IntEnum):
    Open = 1
    UnderReview = 2
    Resolved = 3
    Dismissed = 4


class AIRiskLevel(IntEnum):
    Low = 1
    Medium = 2
    High = 3


def parse_enum(enum: type[IntEnum], text: str | None, ignore_case: bool = True):
    """Like .NET Enum.TryParse(text, ignoreCase): the member by name (or number), else None."""
    if text is None:
        return None
    text = str(text).strip()
    if text.lstrip("-").isdigit():
        try:
            return enum(int(text))
        except ValueError:
            return None
    for member in enum:
        if member.name == text or (ignore_case and member.name.lower() == text.lower()):
            return member
    return None
