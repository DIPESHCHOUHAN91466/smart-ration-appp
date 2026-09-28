"""Time slots, booking tokens and completed collections. Mirrors the existing MySQL schema; see app/models/__init__.py."""

from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.types import DateTime6, LongText, Money, Time6


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
