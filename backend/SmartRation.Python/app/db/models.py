"""SQLAlchemy models mirroring the EXISTING MySQL schema (owned today by EF Core).

Generated from the live database's information_schema and reviewed by hand.
Table/column names, types, nullability, keys, foreign keys and indexes match
the database exactly; tests/test_schema_compat.py fails if they ever drift.
Relationships are added per migration phase, as each router needs them.

Enums are stored as integers, exactly as the C# API stores them.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Double, ForeignKey, Index, Integer, String

from app.db.database import Base
from app.db.types import BigId, DateTime6, LongText, Money, Time6


class AIAlert(Base):
    __tablename__ = "AIAlerts"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    ShopId = Column(Integer, nullable=True)
    BeneficiaryId = Column(Integer, nullable=True)
    AlertType = Column(String(64), nullable=False)
    Severity = Column(Integer, nullable=False)
    Description = Column(LongText, nullable=False)
    Status = Column(Integer, nullable=False)
    CreatedAt = Column(DateTime6, nullable=False)
    ResolvedAt = Column(DateTime6, nullable=True)
    Source = Column(String(32), nullable=False, server_default="RULES")
    Title = Column(String(200), nullable=True)
    RationType = Column(Integer, nullable=True)
    Score = Column(Double, nullable=True)
    RecommendedAction = Column(String(500), nullable=True)
    DedupKey = Column(String(128), nullable=True)
    MetadataJson = Column(LongText, nullable=True)
    DetectedAt = Column(DateTime6, nullable=True)
    LastSeenAt = Column(DateTime6, nullable=True)
    ResolvedByUserId = Column(Integer, nullable=True)
    ResolutionNote = Column(String(500), nullable=True)

    __table_args__ = (
        Index("IX_AIAlerts_DedupKey_Status", "DedupKey", "Status"),
        Index("IX_AIAlerts_ShopId_Status", "ShopId", "Status"),
    )


class AIInsight(Base):
    __tablename__ = "AIInsights"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    EntityType = Column(LongText, nullable=False)
    EntityId = Column(Integer, nullable=True)
    InsightType = Column(LongText, nullable=False)
    RiskLevel = Column(Integer, nullable=False)
    Score = Column(Double, nullable=False)
    Explanation = Column(LongText, nullable=False)
    Recommendation = Column(LongText, nullable=False)
    CreatedAt = Column(DateTime6, nullable=False)


class AadhaarVerification(Base):
    __tablename__ = "AadhaarVerifications"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryId = Column(Integer, ForeignKey("Beneficiaries.Id", ondelete="CASCADE"), nullable=False)
    AadhaarReferenceId = Column(LongText, nullable=False)
    AadhaarMasked = Column(LongText, nullable=False)
    Status = Column(Integer, nullable=False)
    VerificationDate = Column(DateTime6, nullable=True)
    VerificationSource = Column(LongText, nullable=False)
    VerificationMode = Column(LongText, nullable=False)

    __table_args__ = (
        Index("IX_AadhaarVerifications_BeneficiaryId", "BeneficiaryId", unique=True),
    )


class AuditLog(Base):
    __tablename__ = "AuditLogs"
    Id = Column(BigId, primary_key=True, autoincrement=True)
    UserId = Column(Integer, nullable=True)
    Action = Column(LongText, nullable=False)
    EntityName = Column(LongText, nullable=False)
    EntityId = Column(LongText, nullable=True)
    IpAddress = Column(LongText, nullable=True)
    Details = Column(LongText, nullable=True)
    Role = Column(String(32), nullable=True)
    Result = Column(String(16), nullable=True)
    CreatedAt = Column(DateTime6, nullable=False)


class Beneficiary(Base):
    __tablename__ = "Beneficiaries"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryCode = Column(String(255), nullable=False)
    Address = Column(LongText, nullable=False)
    Gender = Column(Integer, nullable=False)
    DateOfBirth = Column(DateTime6, nullable=False)
    Village = Column(LongText, nullable=False)
    District = Column(LongText, nullable=False)
    State = Column(LongText, nullable=False)
    Pincode = Column(LongText, nullable=False)
    ProfilePhotoUrl = Column(LongText, nullable=True)
    UserId = Column(Integer, ForeignKey("Users.Id", ondelete="CASCADE"), nullable=False)
    FamilyId = Column(Integer, ForeignKey("Families.Id", ondelete="RESTRICT"), nullable=False)
    IsActive = Column(Boolean, nullable=False)
    IsBlocked = Column(Boolean, nullable=False)
    DataSource = Column(LongText, nullable=False)
    CreatedAt = Column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_Beneficiaries_BeneficiaryCode", "BeneficiaryCode", unique=True),
        Index("IX_Beneficiaries_FamilyId", "FamilyId"),
        Index("IX_Beneficiaries_UserId", "UserId", unique=True),
    )


class Family(Base):
    __tablename__ = "Families"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    FamilyCode = Column(String(255), nullable=False)
    RationShopId = Column(Integer, ForeignKey("RationShops.Id", ondelete="RESTRICT"), nullable=False)
    RationSchemeId = Column(Integer, ForeignKey("RationSchemes.Id", ondelete="RESTRICT"), nullable=False)
    DataSource = Column(LongText, nullable=False)
    CreatedAt = Column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_Families_FamilyCode", "FamilyCode", unique=True),
        Index("IX_Families_RationSchemeId", "RationSchemeId"),
        Index("IX_Families_RationShopId", "RationShopId"),
    )


class FamilyMember(Base):
    __tablename__ = "FamilyMembers"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    FamilyId = Column(Integer, ForeignKey("Families.Id", ondelete="CASCADE"), nullable=False)
    FullName = Column(LongText, nullable=False)
    Age = Column(Integer, nullable=False)
    Relationship = Column(Integer, nullable=False)
    Eligibility = Column(Integer, nullable=False)
    DataSource = Column(LongText, nullable=False)

    __table_args__ = (
        Index("IX_FamilyMembers_FamilyId", "FamilyId"),
    )


class Inventory(Base):
    __tablename__ = "Inventory"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    RationShopId = Column(Integer, ForeignKey("RationShops.Id", ondelete="CASCADE"), nullable=False)
    RationType = Column(Integer, nullable=False)
    AvailableQuantity = Column(Money, nullable=False)
    AllocatedQuantity = Column(Money, nullable=False)
    MinimumStockLevel = Column(Money, nullable=False)
    UpdatedAt = Column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_Inventory_RationShopId_RationType", "RationShopId", "RationType", unique=True),
    )


class InventoryMovement(Base):
    __tablename__ = "InventoryMovements"
    Id = Column(BigId, primary_key=True, autoincrement=True)
    RationShopId = Column(Integer, ForeignKey("RationShops.Id", ondelete="RESTRICT"), nullable=False)
    RationType = Column(Integer, nullable=False)
    MovementType = Column(Integer, nullable=False)
    Quantity = Column(Money, nullable=False)
    BalanceAfter = Column(Money, nullable=False)
    Reference = Column(String(64), nullable=True)
    Note = Column(String(256), nullable=True)
    RecordedByUserId = Column(Integer, nullable=True)
    CreatedAt = Column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_InventoryMovements_RationShopId_RationType_CreatedAt", "RationShopId", "RationType", "CreatedAt"),
    )


class MobileVerification(Base):
    __tablename__ = "MobileVerifications"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryId = Column(Integer, ForeignKey("Beneficiaries.Id", ondelete="CASCADE"), nullable=False)
    MobileMasked = Column(LongText, nullable=False)
    Status = Column(Integer, nullable=False)
    VerifiedAt = Column(DateTime6, nullable=True)
    VerificationSource = Column(LongText, nullable=False)

    __table_args__ = (
        Index("IX_MobileVerifications_BeneficiaryId", "BeneficiaryId", unique=True),
    )


class Notification(Base):
    __tablename__ = "Notifications"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    UserId = Column(Integer, ForeignKey("Users.Id", ondelete="CASCADE"), nullable=False)
    Type = Column(Integer, nullable=False)
    Title = Column(LongText, nullable=False)
    Message = Column(LongText, nullable=False)
    IsRead = Column(Boolean, nullable=False)
    CreatedAt = Column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_Notifications_UserId", "UserId"),
    )


class OtpVerification(Base):
    __tablename__ = "OtpVerifications"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryId = Column(Integer, ForeignKey("Beneficiaries.Id", ondelete="CASCADE"), nullable=False)
    RequestedByUserId = Column(Integer, nullable=False)
    OtpHash = Column(LongText, nullable=False)
    AttemptCount = Column(Integer, nullable=False)
    MaxAttempts = Column(Integer, nullable=False)
    Status = Column(Integer, nullable=False)
    CreatedAt = Column(DateTime6, nullable=False)
    ExpiresAt = Column(DateTime6, nullable=False)
    VerifiedAt = Column(DateTime6, nullable=True)

    __table_args__ = (
        Index("IX_OtpVerifications_BeneficiaryId", "BeneficiaryId"),
    )


class PassbookVerification(Base):
    __tablename__ = "PassbookVerifications"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    BeneficiaryId = Column(Integer, ForeignKey("Beneficiaries.Id", ondelete="CASCADE"), nullable=False)
    PassbookNumber = Column(LongText, nullable=False)
    Status = Column(LongText, nullable=False)
    VerificationStatus = Column(Integer, nullable=False)
    LastUpdated = Column(DateTime6, nullable=False)
    VerificationSource = Column(LongText, nullable=False)

    __table_args__ = (
        Index("IX_PassbookVerifications_BeneficiaryId", "BeneficiaryId", unique=True),
    )


class RationCollection(Base):
    __tablename__ = "RationCollections"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    CollectionCode = Column(String(255), nullable=False)
    TokenId = Column(Integer, ForeignKey("Tokens.Id", ondelete="RESTRICT"), nullable=False)
    BeneficiaryId = Column(Integer, ForeignKey("Beneficiaries.Id", ondelete="RESTRICT"), nullable=False)
    RationShopId = Column(Integer, ForeignKey("RationShops.Id", ondelete="RESTRICT"), nullable=False)
    OperatorUserId = Column(Integer, nullable=False)
    VerificationMethod = Column(LongText, nullable=False)
    CollectedAt = Column(DateTime6, nullable=False)
    IdempotencyKey = Column(String(64), nullable=True)

    __table_args__ = (
        Index("IX_RationCollections_BeneficiaryId", "BeneficiaryId"),
        Index("IX_RationCollections_CollectionCode", "CollectionCode", unique=True),
        Index("IX_RationCollections_IdempotencyKey", "IdempotencyKey", unique=True),
        Index("IX_RationCollections_RationShopId", "RationShopId"),
        Index("IX_RationCollections_TokenId", "TokenId", unique=True),
    )


class RationCollectionItem(Base):
    __tablename__ = "RationCollectionItems"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    RationCollectionId = Column(Integer, ForeignKey("RationCollections.Id", ondelete="CASCADE"), nullable=False)
    RationType = Column(Integer, nullable=False)
    Quantity = Column(Money, nullable=False)

    __table_args__ = (
        Index("IX_RationCollectionItems_RationCollectionId", "RationCollectionId"),
    )


class RationItem(Base):
    __tablename__ = "RationItems"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    RationType = Column(Integer, nullable=False)
    Name = Column(LongText, nullable=False)
    VernacularName = Column(LongText, nullable=False)
    Unit = Column(LongText, nullable=False)
    StandardQuotaPerBooking = Column(Money, nullable=False)
    IsActive = Column(Boolean, nullable=False)

    __table_args__ = (
        Index("IX_RationItems_RationType", "RationType", unique=True),
    )


class RationScheme(Base):
    __tablename__ = "RationSchemes"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    SchemeCode = Column(String(255), nullable=False)
    Name = Column(LongText, nullable=False)
    Description = Column(LongText, nullable=False)
    IsActive = Column(Boolean, nullable=False)

    __table_args__ = (
        Index("IX_RationSchemes_SchemeCode", "SchemeCode", unique=True),
    )


class RationShop(Base):
    __tablename__ = "RationShops"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    ShopName = Column(LongText, nullable=False)
    ShopCode = Column(String(255), nullable=False)
    Address = Column(LongText, nullable=False)
    District = Column(LongText, nullable=False)
    State = Column(LongText, nullable=False)
    Taluka = Column(LongText, nullable=True)
    Village = Column(LongText, nullable=True)
    Latitude = Column(Double, nullable=False)
    Longitude = Column(Double, nullable=False)
    IsActive = Column(Boolean, nullable=False)
    CreatedAt = Column(DateTime6, nullable=False)

    __table_args__ = (
        Index("IX_RationShops_ShopCode", "ShopCode", unique=True),
    )


class RefreshToken(Base):
    __tablename__ = "RefreshTokens"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    UserId = Column(Integer, ForeignKey("Users.Id", ondelete="CASCADE"), nullable=False)
    TokenHash = Column(String(255), nullable=False)
    ExpiresAt = Column(DateTime6, nullable=False)
    CreatedAt = Column(DateTime6, nullable=False)
    RevokedAt = Column(DateTime6, nullable=True)
    ReplacedByTokenHash = Column(LongText, nullable=True)

    __table_args__ = (
        Index("IX_RefreshTokens_TokenHash", "TokenHash", unique=True),
        Index("IX_RefreshTokens_UserId", "UserId"),
    )


class SchemeEntitlementItem(Base):
    __tablename__ = "SchemeEntitlementItems"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    RationSchemeId = Column(Integer, ForeignKey("RationSchemes.Id", ondelete="CASCADE"), nullable=False)
    RationType = Column(Integer, nullable=False)
    QuotaPerEligibleMemberPerMonth = Column(Money, nullable=False)

    __table_args__ = (
        Index("IX_SchemeEntitlementItems_RationSchemeId_RationType", "RationSchemeId", "RationType", unique=True),
    )


class TimeSlot(Base):
    __tablename__ = "TimeSlots"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    RationShopId = Column(Integer, ForeignKey("RationShops.Id", ondelete="CASCADE"), nullable=False)
    SlotDate = Column(DateTime6, nullable=False)
    StartTime = Column(Time6, nullable=False)
    EndTime = Column(Time6, nullable=False)
    Capacity = Column(Integer, nullable=False)
    BookedCount = Column(Integer, nullable=False)

    __table_args__ = (
        Index("IX_TimeSlots_RationShopId", "RationShopId"),
    )


class Token(Base):
    __tablename__ = "Tokens"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    TokenNumber = Column(String(255), nullable=False)
    UserId = Column(Integer, ForeignKey("Users.Id", ondelete="RESTRICT"), nullable=False)
    RationShopId = Column(Integer, ForeignKey("RationShops.Id", ondelete="RESTRICT"), nullable=False)
    TimeSlotId = Column(Integer, ForeignKey("TimeSlots.Id", ondelete="RESTRICT"), nullable=False)
    Status = Column(Integer, nullable=False)
    QRCodeValue = Column(LongText, nullable=True)
    CreatedAt = Column(DateTime6, nullable=False)
    CollectedAt = Column(DateTime6, nullable=True)

    __table_args__ = (
        Index("IX_Tokens_RationShopId", "RationShopId"),
        Index("IX_Tokens_TimeSlotId", "TimeSlotId"),
        Index("IX_Tokens_TokenNumber", "TokenNumber", unique=True),
        Index("IX_Tokens_UserId", "UserId"),
    )


class TokenItem(Base):
    __tablename__ = "TokenItems"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    TokenId = Column(Integer, ForeignKey("Tokens.Id", ondelete="CASCADE"), nullable=False)
    RationType = Column(Integer, nullable=False)
    Quantity = Column(Money, nullable=False)

    __table_args__ = (
        Index("IX_TokenItems_TokenId", "TokenId"),
    )


class User(Base):
    __tablename__ = "Users"
    Id = Column(Integer, primary_key=True, autoincrement=True)
    FullName = Column(LongText, nullable=False)
    Email = Column(String(255), nullable=False)
    MobileNumber = Column(String(255), nullable=False)
    PasswordHash = Column(LongText, nullable=False)
    Role = Column(Integer, nullable=False)
    IsActive = Column(Boolean, nullable=False)
    CreatedAt = Column(DateTime6, nullable=False)
    RationShopId = Column(Integer, ForeignKey("RationShops.Id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        Index("IX_Users_Email", "Email", unique=True),
        Index("IX_Users_MobileNumber", "MobileNumber", unique=True),
        Index("IX_Users_RationShopId", "RationShopId"),
    )


class VerificationAuditLog(Base):
    __tablename__ = "VerificationAuditLogs"
    Id = Column(BigId, primary_key=True, autoincrement=True)
    VerificationReference = Column(LongText, nullable=True)
    TokenNumber = Column(LongText, nullable=True)
    BeneficiaryId = Column(Integer, nullable=True)
    ShopId = Column(Integer, nullable=True)
    Action = Column(Integer, nullable=False)
    VerificationMethod = Column(LongText, nullable=False)
    Status = Column(LongText, nullable=False)
    Reason = Column(LongText, nullable=True)
    OperatorId = Column(Integer, nullable=True)
    DeviceInfo = Column(LongText, nullable=True)
    IpAddress = Column(LongText, nullable=True)
    Timestamp = Column(DateTime6, nullable=False)
