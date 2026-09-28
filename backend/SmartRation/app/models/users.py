"""Accounts, sign-in sessions and the security audit trail. Mirrors the existing MySQL schema; see app/models/__init__.py."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.types import BigId, DateTime6, LongText


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
