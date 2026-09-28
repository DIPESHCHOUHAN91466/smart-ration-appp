"""Test fixtures: a throwaway SQLite database with the subset of the .NET
schema the service reads, stored the way EF Core's SQLite provider stores it
(decimals and datetimes as TEXT, enums as INTEGER)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine

from ai.configs.settings import Settings
from ai.preprocessing.repository import Repository

from ai_testkit import API_KEY, NOW  # noqa: F401  (shared with the test modules)

SCHEMA = """
CREATE TABLE RationShops (Id INTEGER PRIMARY KEY, ShopName TEXT, ShopCode TEXT, District TEXT, IsActive INTEGER);
CREATE TABLE Inventory (Id INTEGER PRIMARY KEY, RationShopId INTEGER, RationType INTEGER, AvailableQuantity TEXT, AllocatedQuantity TEXT, MinimumStockLevel TEXT, UpdatedAt TEXT);
CREATE TABLE InventoryMovements (Id INTEGER PRIMARY KEY, RationShopId INTEGER, RationType INTEGER, MovementType INTEGER, Quantity TEXT, BalanceAfter TEXT, Reference TEXT, Note TEXT, RecordedByUserId INTEGER, CreatedAt TEXT);
CREATE TABLE TimeSlots (Id INTEGER PRIMARY KEY, RationShopId INTEGER, SlotDate TEXT, StartTime TEXT, EndTime TEXT, Capacity INTEGER, BookedCount INTEGER);
CREATE TABLE Tokens (Id INTEGER PRIMARY KEY, TokenNumber TEXT, UserId INTEGER, RationShopId INTEGER, TimeSlotId INTEGER, Status INTEGER, QRCodeValue TEXT, CreatedAt TEXT, CollectedAt TEXT);
CREATE TABLE TokenItems (Id INTEGER PRIMARY KEY, TokenId INTEGER, RationType INTEGER, Quantity TEXT);
CREATE TABLE RationCollections (Id INTEGER PRIMARY KEY, CollectionCode TEXT, TokenId INTEGER, BeneficiaryId INTEGER, RationShopId INTEGER, OperatorUserId INTEGER, VerificationMethod TEXT, CollectedAt TEXT, IdempotencyKey TEXT);
CREATE TABLE RationCollectionItems (Id INTEGER PRIMARY KEY, RationCollectionId INTEGER, RationType INTEGER, Quantity TEXT);
CREATE TABLE VerificationAuditLogs (Id INTEGER PRIMARY KEY, VerificationReference TEXT, TokenNumber TEXT, BeneficiaryId INTEGER, ShopId INTEGER, Action INTEGER, VerificationMethod TEXT, Status TEXT, Reason TEXT, OperatorId INTEGER, DeviceInfo TEXT, IpAddress TEXT, Timestamp TEXT);
CREATE TABLE Families (Id INTEGER PRIMARY KEY, FamilyCode TEXT, RationShopId INTEGER, RationSchemeId INTEGER);
CREATE TABLE FamilyMembers (Id INTEGER PRIMARY KEY, FamilyId INTEGER, FullName TEXT, Age INTEGER, Relationship INTEGER, Eligibility INTEGER);
CREATE TABLE Beneficiaries (Id INTEGER PRIMARY KEY, BeneficiaryCode TEXT, UserId INTEGER, FamilyId INTEGER, IsActive INTEGER, IsBlocked INTEGER);
CREATE TABLE SchemeEntitlementItems (Id INTEGER PRIMARY KEY, RationSchemeId INTEGER, RationType INTEGER, QuotaPerEligibleMemberPerMonth TEXT);
"""


def ts(value: datetime) -> str:
    """EF Core SQLite datetime text format."""
    return value.strftime("%Y-%m-%d %H:%M:%S")


class Db:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)
        self._ids: dict[str, int] = {}

    def _next(self, table: str) -> int:
        self._ids[table] = self._ids.get(table, 0) + 1
        return self._ids[table]

    def insert(self, table: str, **values) -> int:
        values.setdefault("Id", self._next(table))
        cols = ", ".join(values)
        marks = ", ".join("?" for _ in values)
        self.conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", list(values.values()))
        self.conn.commit()
        return values["Id"]

    # -- convenience builders -------------------------------------------------

    def shop(self, name="Test Shop") -> int:
        return self.insert("RationShops", ShopName=name, ShopCode=name.upper(), District="Nagpur", IsActive=1)

    def beneficiary(self, shop_id: int, user_id: int, eligible_members=2, rice_quota="5") -> int:
        family = self.insert("Families", FamilyCode=f"FAM-{user_id}", RationShopId=shop_id, RationSchemeId=1)
        for i in range(eligible_members):
            self.insert("FamilyMembers", FamilyId=family, FullName=f"M{i}", Age=30, Relationship=1, Eligibility=1)
        if not self.conn.execute("SELECT 1 FROM SchemeEntitlementItems WHERE RationSchemeId=1").fetchone():
            self.insert("SchemeEntitlementItems", RationSchemeId=1, RationType=1, QuotaPerEligibleMemberPerMonth=rice_quota)
        return self.insert("Beneficiaries", BeneficiaryCode=f"BEN-{user_id:04d}", UserId=user_id, FamilyId=family, IsActive=1, IsBlocked=0)

    def token(self, shop_id: int, user_id: int, slot: datetime, status: int, collected_at: datetime | None = None, rice="5") -> int:
        slot_id = self.insert("TimeSlots", RationShopId=shop_id, SlotDate=ts(slot.replace(hour=0, minute=0, second=0)),
                              StartTime=slot.strftime("%H:%M:00"), EndTime=(slot + timedelta(minutes=5)).strftime("%H:%M:00"),
                              Capacity=2, BookedCount=1)
        token = self.insert("Tokens", TokenNumber=f"SR-{slot_id:06d}", UserId=user_id, RationShopId=shop_id, TimeSlotId=slot_id,
                            Status=status, CreatedAt=ts(slot - timedelta(days=1)), CollectedAt=ts(collected_at) if collected_at else None)
        self.insert("TokenItems", TokenId=token, RationType=1, Quantity=rice)
        return token

    def collection(self, shop_id: int, beneficiary_id: int, at: datetime, rice: float = 5, token_id: int | None = None) -> int:
        cid = self.insert("RationCollections", CollectionCode=f"COL-{at:%H%M%S}", TokenId=token_id or 0, BeneficiaryId=beneficiary_id,
                          RationShopId=shop_id, OperatorUserId=1, VerificationMethod="QR", CollectedAt=ts(at))
        self.insert("RationCollectionItems", RationCollectionId=cid, RationType=1, Quantity=str(rice))
        return cid

    def audit(self, beneficiary_id: int | None, shop_id: int, action: int, status: str, at: datetime) -> None:
        self.insert("VerificationAuditLogs", BeneficiaryId=beneficiary_id, ShopId=shop_id, Action=action,
                    VerificationMethod="QR", Status=status, Timestamp=ts(at))


@pytest.fixture
def db(tmp_path):
    return Db(str(tmp_path / "test.db"))


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        db_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        api_key=API_KEY,
        shop_utc_offset_minutes=330,
        forecast_min_history_days=14,
        forecast_default_horizon_days=7,
        low_stock_days=7,
        critical_stock_days=3,
        default_service_minutes=4.0,
        min_service_samples=5,
        analysis_window_days=30,
        log_level="WARNING",
    )


@pytest.fixture
def repo(db, settings) -> Repository:
    return Repository(create_engine(settings.db_url))
