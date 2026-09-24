"""History generator invariants and the monthly-cycle forecast."""

from __future__ import annotations

import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

from smartration_ai import forecasting, shop_monitor
from smartration_ai.domain import MovementType

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import generate_history as gen  # noqa: E402

# The generator's tables, typed the way EF Core's SQLite provider creates them.
SCHEMA = """
CREATE TABLE Users (Id INTEGER PRIMARY KEY, FullName TEXT NOT NULL, Email TEXT NOT NULL UNIQUE, MobileNumber TEXT NOT NULL UNIQUE, PasswordHash TEXT NOT NULL, Role INTEGER NOT NULL, IsActive INTEGER NOT NULL, CreatedAt TEXT NOT NULL, RationShopId INTEGER);
CREATE TABLE RationShops (Id INTEGER PRIMARY KEY, ShopName TEXT, ShopCode TEXT, District TEXT, State TEXT, Village TEXT, IsActive INTEGER);
CREATE TABLE RationSchemes (Id INTEGER PRIMARY KEY, SchemeCode TEXT);
CREATE TABLE SchemeEntitlementItems (Id INTEGER PRIMARY KEY, RationSchemeId INTEGER, RationType INTEGER, QuotaPerEligibleMemberPerMonth TEXT);
CREATE TABLE RationItems (Id INTEGER PRIMARY KEY, RationType INTEGER, StandardQuotaPerBooking TEXT, IsActive INTEGER);
CREATE TABLE Families (Id INTEGER PRIMARY KEY, FamilyCode TEXT NOT NULL UNIQUE, RationShopId INTEGER NOT NULL, RationSchemeId INTEGER NOT NULL, DataSource TEXT NOT NULL, CreatedAt TEXT NOT NULL);
CREATE TABLE FamilyMembers (Id INTEGER PRIMARY KEY, FamilyId INTEGER NOT NULL, FullName TEXT NOT NULL, Age INTEGER NOT NULL, Relationship INTEGER NOT NULL, Eligibility INTEGER NOT NULL, DataSource TEXT NOT NULL);
CREATE TABLE Beneficiaries (Id INTEGER PRIMARY KEY, BeneficiaryCode TEXT NOT NULL UNIQUE, Address TEXT NOT NULL, UserId INTEGER NOT NULL UNIQUE, FamilyId INTEGER NOT NULL, IsActive INTEGER NOT NULL, IsBlocked INTEGER NOT NULL, DataSource TEXT NOT NULL, CreatedAt TEXT NOT NULL, DateOfBirth TEXT NOT NULL, District TEXT NOT NULL, Gender INTEGER NOT NULL, Pincode TEXT NOT NULL, ProfilePhotoUrl TEXT, State TEXT NOT NULL, Village TEXT NOT NULL);
CREATE TABLE Inventory (Id INTEGER PRIMARY KEY, RationShopId INTEGER, RationType INTEGER, AvailableQuantity TEXT, AllocatedQuantity TEXT, MinimumStockLevel TEXT, UpdatedAt TEXT);
CREATE TABLE InventoryMovements (Id INTEGER PRIMARY KEY, RationShopId INTEGER NOT NULL, RationType INTEGER NOT NULL, MovementType INTEGER NOT NULL, Quantity TEXT NOT NULL, BalanceAfter TEXT NOT NULL, Reference TEXT, Note TEXT, RecordedByUserId INTEGER, CreatedAt TEXT NOT NULL);
CREATE TABLE TimeSlots (Id INTEGER PRIMARY KEY, RationShopId INTEGER NOT NULL, SlotDate TEXT NOT NULL, StartTime TEXT NOT NULL, EndTime TEXT NOT NULL, Capacity INTEGER NOT NULL, BookedCount INTEGER NOT NULL);
CREATE TABLE Tokens (Id INTEGER PRIMARY KEY, TokenNumber TEXT NOT NULL UNIQUE, UserId INTEGER NOT NULL, RationShopId INTEGER NOT NULL, TimeSlotId INTEGER NOT NULL, Status INTEGER NOT NULL, QRCodeValue TEXT, CreatedAt TEXT NOT NULL, CollectedAt TEXT);
CREATE TABLE TokenItems (Id INTEGER PRIMARY KEY, TokenId INTEGER NOT NULL, RationType INTEGER NOT NULL, Quantity TEXT NOT NULL);
CREATE TABLE RationCollections (Id INTEGER PRIMARY KEY, CollectionCode TEXT NOT NULL UNIQUE, TokenId INTEGER NOT NULL UNIQUE, BeneficiaryId INTEGER NOT NULL, RationShopId INTEGER NOT NULL, OperatorUserId INTEGER NOT NULL, VerificationMethod TEXT NOT NULL, CollectedAt TEXT NOT NULL, IdempotencyKey TEXT);
CREATE TABLE RationCollectionItems (Id INTEGER PRIMARY KEY, RationCollectionId INTEGER NOT NULL, RationType INTEGER NOT NULL, Quantity TEXT NOT NULL);
CREATE TABLE VerificationAuditLogs (Id INTEGER PRIMARY KEY, VerificationReference TEXT, TokenNumber TEXT, BeneficiaryId INTEGER, ShopId INTEGER, Action INTEGER NOT NULL, VerificationMethod TEXT NOT NULL, Status TEXT NOT NULL, Reason TEXT, OperatorId INTEGER, DeviceInfo TEXT, IpAddress TEXT, Timestamp TEXT NOT NULL);
INSERT INTO RationShops VALUES (1,'A','SHOP-A','Nagpur','Maharashtra','A',1),(2,'B','SHOP-B','Nagpur','Maharashtra','B',1);
INSERT INTO RationSchemes VALUES (1,'NFSA');
INSERT INTO SchemeEntitlementItems VALUES (1,1,1,'5.0'),(2,1,2,'3.0'),(3,1,3,'1.0');
INSERT INTO RationItems VALUES (1,1,'5.0',1),(2,2,'5.0',1),(3,3,'1.0',1);
INSERT INTO Users VALUES (1,'Owner','owner@x.test','9000000001','h',2,1,'2026-01-01 00:00:00',1);
INSERT INTO Inventory VALUES (1,1,1,'80','0','30','2026-01-01'),(2,1,2,'60','0','30','2026-01-01'),(3,1,3,'9','0','20','2026-01-01'),
                             (4,2,1,'40','0','30','2026-01-01'),(5,2,2,'35','0','30','2026-01-01'),(6,2,3,'12','0','20','2026-01-01');
INSERT INTO TimeSlots VALUES (1,1,'2026-09-17 00:00:00','09:00:00','09:05:00',2,0);
"""


def make_db(tmp_path) -> str:
    path = tmp_path / "gen.db"
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    return f"sqlite:///{path.as_posix()}"


def run(url, *extra):
    return gen.main(["--db-url", url, "--months", "4", "--households-per-shop", "6", "--seed", "7", "--today", "2026-09-24", *extra])


def counts(url):
    conn = sqlite3.connect(url.removeprefix("sqlite:///"))
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("RationCollections", "RationCollectionItems", "InventoryMovements", "Beneficiaries", "Users")}
    finally:
        conn.close()


def test_generator_writes_consistent_history(tmp_path, capsys):
    url = make_db(tmp_path)
    assert run(url) == 0
    c = counts(url)
    assert c["RationCollections"] > 100 and c["Beneficiaries"] == 12
    assert gen.main(["--db-url", url, "--verify"]) == 0  # entitlement, caps, no negative stock, ledger chain, end balance


def test_generator_is_deterministic_and_replace_is_clean(tmp_path):
    url = make_db(tmp_path)
    run(url)
    first = counts(url)
    assert run(url) == 3  # refuses to double-generate
    assert run(url, "--replace") == 0
    assert counts(url) == first  # same seed -> same data, nothing left behind


def test_dry_run_writes_nothing(tmp_path):
    url = make_db(tmp_path)
    assert run(url, "--dry-run") == 0
    assert counts(url)["RationCollections"] == 0 and counts(url)["Users"] == 1


def test_generated_accounts_cannot_log_in(tmp_path):
    url = make_db(tmp_path)
    run(url)
    conn = sqlite3.connect(url.removeprefix("sqlite:///"))
    hashes = [r[0] for r in conn.execute("SELECT PasswordHash FROM Users WHERE Email LIKE '%@history.synthetic.invalid'")]
    conn.close()
    assert hashes and all(h.startswith("$2a$11$") and len(h) == 60 for h in hashes)


def test_verify_detects_a_broken_ledger(tmp_path):
    url = make_db(tmp_path)
    run(url)
    conn = sqlite3.connect(url.removeprefix("sqlite:///"))
    conn.execute("UPDATE InventoryMovements SET BalanceAfter = '-5' WHERE Id = (SELECT MAX(Id) FROM InventoryMovements WHERE MovementType = 2)")
    conn.commit()
    conn.close()
    assert gen.main(["--db-url", url, "--verify"]) == 1


# ---------------------------------------------------------------- forecasting on a monthly cycle


def test_monthly_cycle_is_learned_and_confident():
    cycle = [30.0] * 10 + [5.0] * 20  # most families collect early in the month
    history = cycle * 6
    r = forecasting.forecast(history, 30, 14)
    assert r.method == "monthly-cycle seasonal average"
    assert abs(r.forecast_total - sum(cycle)) < 1
    assert r.confidence == "HIGH" and r.backtest_wmape < 0.05


def test_damage_rate_uses_stock_handled_in_window():
    start = datetime(2026, 9, 1)
    mv = [
        {"id": 1, "shop_id": 1, "ration_type": 1, "type": MovementType.RECEIVED, "quantity": 500.0, "balance_after": 500.0, "at": datetime(2026, 8, 1)},
        {"id": 2, "shop_id": 1, "ration_type": 1, "type": MovementType.DAMAGED, "quantity": 40.0, "balance_after": 460.0, "at": datetime(2026, 9, 5)},
    ]
    inv = [{"shop_id": 1, "ration_type": 1, "available": 460.0}]
    out = shop_monitor.analyse([{"Id": 1, "ShopName": "S"}], [], {}, [], [], mv, inv, date(2026, 9, 24), "en", window_start=start)[0]
    assert [f["code"] for f in out["findings"]] == ["SHOP_HIGH_DAMAGE"]  # 40 of 500 handled = 8%, no receipt in window
