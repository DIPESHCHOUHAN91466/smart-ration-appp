"""Fair-price shops, ration items and stock. Mirrors the existing MySQL schema; see app/models/__init__.py."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Double, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.types import BigId, DateTime6, LongText, Money


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

    __table_args__ = (
        Index("IX_InventoryMovements_RationShopId_RationType_CreatedAt", "RationShopId", "RationType", "CreatedAt"),
    )
