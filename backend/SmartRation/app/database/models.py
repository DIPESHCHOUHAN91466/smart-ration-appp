"""SQLAlchemy models: all 25 tables in one file, grouped by domain, matching the MySQL schema (owned by the Alembic migrations in migrations/).

Generated from the live database's information_schema and reviewed by hand.
Table/column names, types, nullability, keys, foreign keys and indexes match
the database exactly; tests/integration/test_schema_compat.py fails if they ever drift.
Relationships are added per migration phase, as each router needs them.

Enums are stored as integers, exactly as the C# API stores them.
"""

from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, Double, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.types import BigId, DateTime6, LongText, Money, Time6

# ---------------- users: Accounts, sign-in sessions and the security audit trail.


class User(Base):
    __tablename__ = "Users"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    FullName: Mapped[str] = mapped_column(LongText, nullable=False)
    Email: Mapped[str] = mapped_column(String(255), nullable=False)
    MobileNumber: Mapped[str] = mapped_column(String(255), nullable=False)
    PasswordHash: Mapped[str] = mapped_column(LongText, nullable=False)
    Role: Mapped[int] = mapped_column(Integer, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    RationShopId: Mapped[int | None] = mapped_column(Integer, ForeignKey("RationShops.Id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        Index("IX_Users_Email", "Email", unique=True),
        Index("IX_Users_MobileNumber", "MobileNumber", unique=True),
        Index("IX_Users_RationShopId", "RationShopId"),
    )


class RefreshToken(Base):
    __tablename__ = "RefreshTokens"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("Users.Id", ondelete="CASCADE"), nullable=False)
    TokenHash: Mapped[str] = mapped_column(String(255), nullable=False)
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    RevokedAt: Mapped[datetime | None] = mapped_column(DateTime6, nullable=True)
    ReplacedByTokenHash: Mapped[str | None] = mapped_column(LongText, nullable=True)

    __table_args__ = (
        Index("IX_RefreshTokens_TokenHash", "TokenHash", unique=True),
        Index("IX_RefreshTokens_UserId", "UserId"),
    )


class AuditLog(Base):
    __tablename__ = "AuditLogs"
    Id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    UserId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    Action: Mapped[str] = mapped_column(LongText, nullable=False)
    EntityName: Mapped[str] = mapped_column(LongText, nullable=False)
    EntityId: Mapped[str | None] = mapped_column(LongText, nullable=True)
    IpAddress: Mapped[str | None] = mapped_column(LongText, nullable=True)
    Details: Mapped[str | None] = mapped_column(LongText, nullable=True)
    Role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    Result: Mapped[str | None] = mapped_column(String(16), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)


class Notification(Base):
    __tablename__ = "Notifications"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("Users.Id", ondelete="CASCADE"), nullable=False)
    Type: Mapped[int] = mapped_column(Integer, nullable=False)
    Title: Mapped[str] = mapped_column(LongText, nullable=False)
    Message: Mapped[str] = mapped_column(LongText, nullable=False)
    IsRead: Mapped[bool] = mapped_column(Boolean, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_Notifications_UserId", "UserId"),
    )


# ---------------- verification: Identity checks: Aadhaar (masked, synthetic in development), passbook, mobile and OTP.


class AadhaarVerification(Base):
    __tablename__ = "AadhaarVerifications"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryId: Mapped[int] = mapped_column(Integer, ForeignKey("Beneficiaries.Id", ondelete="CASCADE"), nullable=False)
    AadhaarReferenceId: Mapped[str] = mapped_column(LongText, nullable=False)
    AadhaarMasked: Mapped[str] = mapped_column(LongText, nullable=False)
    Status: Mapped[int] = mapped_column(Integer, nullable=False)
    VerificationDate: Mapped[datetime | None] = mapped_column(DateTime6, nullable=True)
    VerificationSource: Mapped[str] = mapped_column(LongText, nullable=False)
    VerificationMode: Mapped[str] = mapped_column(LongText, nullable=False)

    __table_args__ = (
        Index("IX_AadhaarVerifications_BeneficiaryId", "BeneficiaryId", unique=True),
    )


class PassbookVerification(Base):
    __tablename__ = "PassbookVerifications"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryId: Mapped[int] = mapped_column(Integer, ForeignKey("Beneficiaries.Id", ondelete="CASCADE"), nullable=False)
    PassbookNumber: Mapped[str] = mapped_column(LongText, nullable=False)
    Status: Mapped[str] = mapped_column(LongText, nullable=False)
    VerificationStatus: Mapped[int] = mapped_column(Integer, nullable=False)
    LastUpdated: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    VerificationSource: Mapped[str] = mapped_column(LongText, nullable=False)

    __table_args__ = (
        Index("IX_PassbookVerifications_BeneficiaryId", "BeneficiaryId", unique=True),
    )


class MobileVerification(Base):
    __tablename__ = "MobileVerifications"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryId: Mapped[int] = mapped_column(Integer, ForeignKey("Beneficiaries.Id", ondelete="CASCADE"), nullable=False)
    MobileMasked: Mapped[str] = mapped_column(LongText, nullable=False)
    Status: Mapped[int] = mapped_column(Integer, nullable=False)
    VerifiedAt: Mapped[datetime | None] = mapped_column(DateTime6, nullable=True)
    VerificationSource: Mapped[str] = mapped_column(LongText, nullable=False)

    __table_args__ = (
        Index("IX_MobileVerifications_BeneficiaryId", "BeneficiaryId", unique=True),
    )


class OtpVerification(Base):
    __tablename__ = "OtpVerifications"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryId: Mapped[int] = mapped_column(Integer, ForeignKey("Beneficiaries.Id", ondelete="CASCADE"), nullable=False)
    RequestedByUserId: Mapped[int] = mapped_column(Integer, nullable=False)
    OtpHash: Mapped[str] = mapped_column(LongText, nullable=False)
    AttemptCount: Mapped[int] = mapped_column(Integer, nullable=False)
    MaxAttempts: Mapped[int] = mapped_column(Integer, nullable=False)
    Status: Mapped[int] = mapped_column(Integer, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    ExpiresAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    VerifiedAt: Mapped[datetime | None] = mapped_column(DateTime6, nullable=True)

    __table_args__ = (
        Index("IX_OtpVerifications_BeneficiaryId", "BeneficiaryId"),
    )


class VerificationAuditLog(Base):
    __tablename__ = "VerificationAuditLogs"
    Id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    VerificationReference: Mapped[str | None] = mapped_column(LongText, nullable=True)
    TokenNumber: Mapped[str | None] = mapped_column(LongText, nullable=True)
    BeneficiaryId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ShopId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    Action: Mapped[int] = mapped_column(Integer, nullable=False)
    VerificationMethod: Mapped[str] = mapped_column(LongText, nullable=False)
    Status: Mapped[str] = mapped_column(LongText, nullable=False)
    Reason: Mapped[str | None] = mapped_column(LongText, nullable=True)
    OperatorId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    DeviceInfo: Mapped[str | None] = mapped_column(LongText, nullable=True)
    IpAddress: Mapped[str | None] = mapped_column(LongText, nullable=True)
    Timestamp: Mapped[datetime] = mapped_column(DateTime6, nullable=False)


# ---------------- beneficiaries: Ration-card holders and their families.


class Beneficiary(Base):
    __tablename__ = "Beneficiaries"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryCode: Mapped[str] = mapped_column(String(255), nullable=False)
    Address: Mapped[str] = mapped_column(LongText, nullable=False)
    Gender: Mapped[int] = mapped_column(Integer, nullable=False)
    DateOfBirth: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    Village: Mapped[str] = mapped_column(LongText, nullable=False)
    District: Mapped[str] = mapped_column(LongText, nullable=False)
    State: Mapped[str] = mapped_column(LongText, nullable=False)
    Pincode: Mapped[str] = mapped_column(LongText, nullable=False)
    ProfilePhotoUrl: Mapped[str | None] = mapped_column(LongText, nullable=True)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("Users.Id", ondelete="CASCADE"), nullable=False)
    FamilyId: Mapped[int] = mapped_column(Integer, ForeignKey("Families.Id", ondelete="RESTRICT"), nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    IsBlocked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    DataSource: Mapped[str] = mapped_column(LongText, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_Beneficiaries_BeneficiaryCode", "BeneficiaryCode", unique=True),
        Index("IX_Beneficiaries_FamilyId", "FamilyId"),
        Index("IX_Beneficiaries_UserId", "UserId", unique=True),
    )


class Family(Base):
    __tablename__ = "Families"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    FamilyCode: Mapped[str] = mapped_column(String(255), nullable=False)
    RationShopId: Mapped[int] = mapped_column(Integer, ForeignKey("RationShops.Id", ondelete="RESTRICT"), nullable=False)
    RationSchemeId: Mapped[int] = mapped_column(Integer, ForeignKey("RationSchemes.Id", ondelete="RESTRICT"), nullable=False)
    DataSource: Mapped[str] = mapped_column(LongText, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_Families_FamilyCode", "FamilyCode", unique=True),
        Index("IX_Families_RationSchemeId", "RationSchemeId"),
        Index("IX_Families_RationShopId", "RationShopId"),
    )


class FamilyMember(Base):
    __tablename__ = "FamilyMembers"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    FamilyId: Mapped[int] = mapped_column(Integer, ForeignKey("Families.Id", ondelete="CASCADE"), nullable=False)
    FullName: Mapped[str] = mapped_column(LongText, nullable=False)
    Age: Mapped[int] = mapped_column(Integer, nullable=False)
    Relationship: Mapped[int] = mapped_column(Integer, nullable=False)
    Eligibility: Mapped[int] = mapped_column(Integer, nullable=False)
    DataSource: Mapped[str] = mapped_column(LongText, nullable=False)
    # Gender enum (1 Male, 2 Female, 3 Other); NULL = not recorded. Added in migration 0002.
    Gender: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("IX_FamilyMembers_FamilyId", "FamilyId"),
    )


# ---------------- shops: Fair-price shops, ration items and stock.


class RationShop(Base):
    __tablename__ = "RationShops"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ShopName: Mapped[str] = mapped_column(LongText, nullable=False)
    ShopCode: Mapped[str] = mapped_column(String(255), nullable=False)
    Address: Mapped[str] = mapped_column(LongText, nullable=False)
    District: Mapped[str] = mapped_column(LongText, nullable=False)
    State: Mapped[str] = mapped_column(LongText, nullable=False)
    Taluka: Mapped[str | None] = mapped_column(LongText, nullable=True)
    Village: Mapped[str | None] = mapped_column(LongText, nullable=True)
    Latitude: Mapped[float] = mapped_column(Double, nullable=False)
    Longitude: Mapped[float] = mapped_column(Double, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_RationShops_ShopCode", "ShopCode", unique=True),
    )


class RationItem(Base):
    __tablename__ = "RationItems"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RationType: Mapped[int] = mapped_column(Integer, nullable=False)
    Name: Mapped[str] = mapped_column(LongText, nullable=False)
    VernacularName: Mapped[str] = mapped_column(LongText, nullable=False)
    Unit: Mapped[str] = mapped_column(LongText, nullable=False)
    StandardQuotaPerBooking: Mapped[Decimal] = mapped_column(Money, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, nullable=False)

    __table_args__ = (
        Index("IX_RationItems_RationType", "RationType", unique=True),
    )


class Inventory(Base):
    __tablename__ = "Inventory"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RationShopId: Mapped[int] = mapped_column(Integer, ForeignKey("RationShops.Id", ondelete="CASCADE"), nullable=False)
    RationType: Mapped[int] = mapped_column(Integer, nullable=False)
    AvailableQuantity: Mapped[Decimal] = mapped_column(Money, nullable=False)
    AllocatedQuantity: Mapped[Decimal] = mapped_column(Money, nullable=False)
    MinimumStockLevel: Mapped[Decimal] = mapped_column(Money, nullable=False)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_Inventory_RationShopId_RationType", "RationShopId", "RationType", unique=True),
    )


class InventoryMovement(Base):
    __tablename__ = "InventoryMovements"
    Id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    RationShopId: Mapped[int] = mapped_column(Integer, ForeignKey("RationShops.Id", ondelete="RESTRICT"), nullable=False)
    RationType: Mapped[int] = mapped_column(Integer, nullable=False)
    MovementType: Mapped[int] = mapped_column(Integer, nullable=False)
    Quantity: Mapped[Decimal] = mapped_column(Money, nullable=False)
    BalanceAfter: Mapped[Decimal] = mapped_column(Money, nullable=False)
    Reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    Note: Mapped[str | None] = mapped_column(String(256), nullable=True)
    RecordedByUserId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    # The client's Idempotency-Key for a delivery / write-off, so a retried request is recorded once.
    IdempotencyKey: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("IX_InventoryMovements_RationShopId_RationType_CreatedAt", "RationShopId", "RationType", "CreatedAt"),
        Index("IX_InventoryMovements_IdempotencyKey", "IdempotencyKey", unique=True),
    )


# ---------------- schemes: Ration schemes and what each entitles a card holder to.


class RationScheme(Base):
    __tablename__ = "RationSchemes"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    SchemeCode: Mapped[str] = mapped_column(String(255), nullable=False)
    Name: Mapped[str] = mapped_column(LongText, nullable=False)
    Description: Mapped[str] = mapped_column(LongText, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, nullable=False)

    __table_args__ = (
        Index("IX_RationSchemes_SchemeCode", "SchemeCode", unique=True),
    )


class SchemeEntitlementItem(Base):
    __tablename__ = "SchemeEntitlementItems"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RationSchemeId: Mapped[int] = mapped_column(Integer, ForeignKey("RationSchemes.Id", ondelete="CASCADE"), nullable=False)
    RationType: Mapped[int] = mapped_column(Integer, nullable=False)
    QuotaPerEligibleMemberPerMonth: Mapped[Decimal] = mapped_column(Money, nullable=False)

    __table_args__ = (
        Index("IX_SchemeEntitlementItems_RationSchemeId_RationType", "RationSchemeId", "RationType", unique=True),
    )


# ---------------- bookings: Time slots, booking tokens and completed collections.


class TimeSlot(Base):
    __tablename__ = "TimeSlots"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RationShopId: Mapped[int] = mapped_column(Integer, ForeignKey("RationShops.Id", ondelete="CASCADE"), nullable=False)
    SlotDate: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    StartTime: Mapped[time] = mapped_column(Time6, nullable=False)
    EndTime: Mapped[time] = mapped_column(Time6, nullable=False)
    Capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    BookedCount: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("IX_TimeSlots_RationShopId", "RationShopId"),
    )


class Token(Base):
    __tablename__ = "Tokens"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    TokenNumber: Mapped[str] = mapped_column(String(255), nullable=False)
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("Users.Id", ondelete="RESTRICT"), nullable=False)
    RationShopId: Mapped[int] = mapped_column(Integer, ForeignKey("RationShops.Id", ondelete="RESTRICT"), nullable=False)
    TimeSlotId: Mapped[int] = mapped_column(Integer, ForeignKey("TimeSlots.Id", ondelete="RESTRICT"), nullable=False)
    Status: Mapped[int] = mapped_column(Integer, nullable=False)
    QRCodeValue: Mapped[str | None] = mapped_column(LongText, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    CollectedAt: Mapped[datetime | None] = mapped_column(DateTime6, nullable=True)

    __table_args__ = (
        Index("IX_Tokens_RationShopId", "RationShopId"),
        Index("IX_Tokens_TimeSlotId", "TimeSlotId"),
        Index("IX_Tokens_TokenNumber", "TokenNumber", unique=True),
        Index("IX_Tokens_UserId", "UserId"),
    )


class TokenItem(Base):
    __tablename__ = "TokenItems"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    TokenId: Mapped[int] = mapped_column(Integer, ForeignKey("Tokens.Id", ondelete="CASCADE"), nullable=False)
    RationType: Mapped[int] = mapped_column(Integer, nullable=False)
    Quantity: Mapped[Decimal] = mapped_column(Money, nullable=False)

    __table_args__ = (
        Index("IX_TokenItems_TokenId", "TokenId"),
    )


class RationCollection(Base):
    __tablename__ = "RationCollections"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CollectionCode: Mapped[str] = mapped_column(String(255), nullable=False)
    TokenId: Mapped[int] = mapped_column(Integer, ForeignKey("Tokens.Id", ondelete="RESTRICT"), nullable=False)
    BeneficiaryId: Mapped[int] = mapped_column(Integer, ForeignKey("Beneficiaries.Id", ondelete="RESTRICT"), nullable=False)
    RationShopId: Mapped[int] = mapped_column(Integer, ForeignKey("RationShops.Id", ondelete="RESTRICT"), nullable=False)
    OperatorUserId: Mapped[int] = mapped_column(Integer, nullable=False)
    VerificationMethod: Mapped[str] = mapped_column(LongText, nullable=False)
    CollectedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    IdempotencyKey: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("IX_RationCollections_BeneficiaryId", "BeneficiaryId"),
        Index("IX_RationCollections_CollectionCode", "CollectionCode", unique=True),
        Index("IX_RationCollections_IdempotencyKey", "IdempotencyKey", unique=True),
        Index("IX_RationCollections_RationShopId", "RationShopId"),
        Index("IX_RationCollections_TokenId", "TokenId", unique=True),
    )


class RationCollectionItem(Base):
    __tablename__ = "RationCollectionItems"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    RationCollectionId: Mapped[int] = mapped_column(Integer, ForeignKey("RationCollections.Id", ondelete="CASCADE"), nullable=False)
    RationType: Mapped[int] = mapped_column(Integer, nullable=False)
    Quantity: Mapped[Decimal] = mapped_column(Money, nullable=False)

    __table_args__ = (
        Index("IX_RationCollectionItems_RationCollectionId", "RationCollectionId"),
    )


# ---------------- grievances: Citizens' complaints, each with a reference number.


class Grievance(Base):
    __tablename__ = "Grievances"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ReferenceNumber: Mapped[str] = mapped_column(String(32), nullable=False)     # GRV-2026-000123
    UserId: Mapped[int] = mapped_column(Integer, ForeignKey("Users.Id", ondelete="RESTRICT"), nullable=False)
    RationShopId: Mapped[int | None] = mapped_column(Integer, ForeignKey("RationShops.Id", ondelete="RESTRICT"), nullable=True)
    Category: Mapped[int] = mapped_column(Integer, nullable=False)             # GrievanceCategory
    RationType: Mapped[int | None] = mapped_column(Integer, nullable=True)     # the item concerned, when there is one
    Description: Mapped[str] = mapped_column(String(1000), nullable=False)
    Status: Mapped[int] = mapped_column(Integer, nullable=False)               # GrievanceStatus
    # How the form was filled: "APP" (typed) or "ASSISTANT" (pre-filled by the AI assistant, then reviewed).
    Source: Mapped[str] = mapped_column(String(16), nullable=False, server_default="APP")
    IdempotencyKey: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ResolutionNote: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ResolvedByUserId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_Grievances_ReferenceNumber", "ReferenceNumber", unique=True),
        Index("IX_Grievances_IdempotencyKey", "IdempotencyKey", unique=True),
        Index("IX_Grievances_UserId_CreatedAt", "UserId", "CreatedAt"),
        Index("IX_Grievances_Status_CreatedAt", "Status", "CreatedAt"),
        Index("IX_Grievances_RationShopId_Status", "RationShopId", "Status"),
    )


# ---------------- ai: Alerts and insights written by the AI service.


class AIAlert(Base):
    __tablename__ = "AIAlerts"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ShopId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    BeneficiaryId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    AlertType: Mapped[str] = mapped_column(String(64), nullable=False)
    Severity: Mapped[int] = mapped_column(Integer, nullable=False)
    Description: Mapped[str] = mapped_column(LongText, nullable=False)
    Status: Mapped[int] = mapped_column(Integer, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
    ResolvedAt: Mapped[datetime | None] = mapped_column(DateTime6, nullable=True)
    Source: Mapped[str] = mapped_column(String(32), nullable=False, server_default="RULES")
    Title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    RationType: Mapped[int | None] = mapped_column(Integer, nullable=True)
    Score: Mapped[float | None] = mapped_column(Double, nullable=True)
    RecommendedAction: Mapped[str | None] = mapped_column(String(500), nullable=True)
    DedupKey: Mapped[str | None] = mapped_column(String(128), nullable=True)
    MetadataJson: Mapped[str | None] = mapped_column(LongText, nullable=True)
    DetectedAt: Mapped[datetime | None] = mapped_column(DateTime6, nullable=True)
    LastSeenAt: Mapped[datetime | None] = mapped_column(DateTime6, nullable=True)
    ResolvedByUserId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ResolutionNote: Mapped[str | None] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("IX_AIAlerts_DedupKey_Status", "DedupKey", "Status"),
        Index("IX_AIAlerts_ShopId_Status", "ShopId", "Status"),
    )


class AIInsight(Base):
    __tablename__ = "AIInsights"
    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    EntityType: Mapped[str] = mapped_column(LongText, nullable=False)
    EntityId: Mapped[int | None] = mapped_column(Integer, nullable=True)
    InsightType: Mapped[str] = mapped_column(LongText, nullable=False)
    RiskLevel: Mapped[int] = mapped_column(Integer, nullable=False)
    Score: Mapped[float] = mapped_column(Double, nullable=False)
    Explanation: Mapped[str] = mapped_column(LongText, nullable=False)
    Recommendation: Mapped[str] = mapped_column(LongText, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime6, nullable=False)
