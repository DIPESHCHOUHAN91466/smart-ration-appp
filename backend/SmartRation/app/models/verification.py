"""Identity checks: Aadhaar (masked, synthetic in development), passbook, mobile and OTP. Mirrors the existing MySQL schema; see app/models/__init__.py."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.types import BigId, DateTime6, LongText


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
