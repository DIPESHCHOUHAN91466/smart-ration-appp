"""Alerts and insights written by the AI service. Mirrors the existing MySQL schema; see app/models/__init__.py."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Double, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.types import DateTime6, LongText


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
