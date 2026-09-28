"""SQLAlchemy models, one module per domain, mirroring the EXISTING MySQL schema (owned today by EF Core).

Generated from the live database's information_schema and reviewed by hand.
Table/column names, types, nullability, keys, foreign keys and indexes match
the database exactly; tests/integration/test_schema_compat.py fails if they ever drift.
Relationships are added per migration phase, as each router needs them.

Enums are stored as integers, exactly as the C# API stores them.
"""

from app.models.ai import AIAlert, AIInsight
from app.models.beneficiaries import Beneficiary, Family, FamilyMember
from app.models.bookings import RationCollection, RationCollectionItem, TimeSlot, Token, TokenItem
from app.models.schemes import RationScheme, SchemeEntitlementItem
from app.models.shops import Inventory, InventoryMovement, RationItem, RationShop
from app.models.users import AuditLog, Notification, RefreshToken, User
from app.models.verification import AadhaarVerification, MobileVerification, OtpVerification, PassbookVerification, VerificationAuditLog

__all__ = [
    "AIAlert",
    "AIInsight",
    "AadhaarVerification",
    "AuditLog",
    "Beneficiary",
    "Family",
    "FamilyMember",
    "Inventory",
    "InventoryMovement",
    "MobileVerification",
    "Notification",
    "OtpVerification",
    "PassbookVerification",
    "RationCollection",
    "RationCollectionItem",
    "RationItem",
    "RationScheme",
    "RationShop",
    "RefreshToken",
    "SchemeEntitlementItem",
    "TimeSlot",
    "Token",
    "TokenItem",
    "User",
    "VerificationAuditLog",
]
