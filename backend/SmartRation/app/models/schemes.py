"""Ration schemes and what each entitles a card holder to. Mirrors the existing MySQL schema; see app/models/__init__.py."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.types import LongText, Money


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
