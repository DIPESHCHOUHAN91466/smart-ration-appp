"""Ration-card holders and their families. Mirrors the existing MySQL schema; see app/models/__init__.py."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.types import DateTime6, LongText


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

    __table_args__ = (
        Index("IX_FamilyMembers_FamilyId", "FamilyId"),
    )
