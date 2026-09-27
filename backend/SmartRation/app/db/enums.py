"""Enums stored as integers, with the same values as the C# models.

`.name` gives the exact string the C# API returns in JSON (e.g. "ShopOwner").
Keep in sync with backend/SmartRation.Api/Models.
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
