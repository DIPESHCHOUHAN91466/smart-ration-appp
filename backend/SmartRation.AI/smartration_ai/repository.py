"""Read-only data access over the .NET-owned schema.

Uses SQLAlchemy Core with reflected tables: every query is parameterized and
dialect-quoted, so the same code works on MySQL and SQLite. Queries are always
bounded by a date window — no full-table loads. Analytics modules receive
plain dicts and never touch the database.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import MetaData, Table, and_, create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchTableError, SQLAlchemyError

from .domain import as_date, as_datetime, as_float, as_time
from .errors import DatabaseUnavailable

log = logging.getLogger(__name__)

REQUIRED_TABLES = [
    "Inventory", "RationCollections", "RationCollectionItems", "Tokens", "TokenItems",
    "TimeSlots", "RationShops", "VerificationAuditLogs", "Beneficiaries", "Families",
    "FamilyMembers", "SchemeEntitlementItems",
]
# Added by a later migration; analytics degrade gracefully without it.
OPTIONAL_TABLES = ["InventoryMovements"]


def create_db_engine(db_url: str) -> Engine:
    kwargs = {"pool_pre_ping": True, "future": True}
    if not db_url.startswith("sqlite"):
        kwargs.update(pool_recycle=1800, pool_size=5, max_overflow=5, connect_args={"connect_timeout": 5})
    return create_engine(db_url, **kwargs)


class Repository:
    def __init__(self, engine: Engine):
        self.engine = engine
        self._tables: dict[str, Table] | None = None

    # ---- infrastructure -------------------------------------------------

    def ping(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            log.warning("Database ping failed")
            return False

    @property
    def t(self) -> dict[str, Table]:
        if self._tables is None:
            try:
                metadata = MetaData()
                tables = {name: Table(name, metadata, autoload_with=self.engine) for name in REQUIRED_TABLES}
                for name in OPTIONAL_TABLES:
                    try:
                        tables[name] = Table(name, metadata, autoload_with=self.engine)
                    except NoSuchTableError:
                        log.info("Optional table %s not present yet", name)
                self._tables = tables
            except SQLAlchemyError as exc:
                log.error("Schema reflection failed: %s", type(exc).__name__)
                raise DatabaseUnavailable() from exc
        return self._tables

    def _p(self, value: datetime):
        """Datetime parameter in the form the column stores: SQLite keeps EF
        datetimes as ISO text (compared lexically), MySQL as DATETIME."""
        if self.engine.dialect.name == "sqlite":
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return value

    def has_table(self, name: str) -> bool:
        return name in self.t

    def _fetch(self, statement) -> list[dict]:
        try:
            with self.engine.connect() as conn:
                return [dict(row._mapping) for row in conn.execute(statement)]
        except SQLAlchemyError as exc:
            log.error("Query failed: %s", type(exc).__name__)
            raise DatabaseUnavailable() from exc

    # ---- reads ------------------------------------------------------------

    def shops(self, shop_id: int | None = None) -> list[dict]:
        s = self.t["RationShops"]
        q = select(s.c.Id, s.c.ShopName, s.c.ShopCode, s.c.District).where(s.c.IsActive == True)  # noqa: E712
        if shop_id is not None:
            q = q.where(s.c.Id == shop_id)
        return self._fetch(q.order_by(s.c.Id))

    def distributed_items(self, since: datetime, shop_id: int | None = None) -> list[dict]:
        """Every issued item since `since`: verified collections plus the older
        quick-complete path (completed tokens without a RationCollection row)."""
        c, ci = self.t["RationCollections"], self.t["RationCollectionItems"]
        q1 = (
            select(c.c.RationShopId.label("shop_id"), c.c.BeneficiaryId.label("beneficiary_id"),
                   c.c.CollectedAt.label("at"), ci.c.RationType.label("ration_type"), ci.c.Quantity.label("quantity"))
            .select_from(ci.join(c, ci.c.RationCollectionId == c.c.Id))
            .where(c.c.CollectedAt >= self._p(since))
        )
        tk, ti = self.t["Tokens"], self.t["TokenItems"]
        q2 = (
            select(tk.c.RationShopId.label("shop_id"), tk.c.CollectedAt.label("at"),
                   ti.c.RationType.label("ration_type"), ti.c.Quantity.label("quantity"))
            .select_from(ti.join(tk, ti.c.TokenId == tk.c.Id))
            .where(and_(tk.c.Status == 3, tk.c.CollectedAt >= self._p(since), ~tk.c.Id.in_(select(c.c.TokenId))))
        )
        if shop_id is not None:
            q1 = q1.where(c.c.RationShopId == shop_id)
            q2 = q2.where(tk.c.RationShopId == shop_id)
        rows = self._fetch(q1) + [{**r, "beneficiary_id": None} for r in self._fetch(q2)]
        return [
            {**r, "at": as_datetime(r["at"]), "quantity": as_float(r["quantity"])}
            for r in rows if r["at"] is not None
        ]

    def first_distribution_at(self, shop_id: int | None = None) -> datetime | None:
        c = self.t["RationCollections"]
        q = select(func.min(c.c.CollectedAt).label("first"))
        if shop_id is not None:
            q = q.where(c.c.RationShopId == shop_id)
        rows = self._fetch(q)
        return as_datetime(rows[0]["first"]) if rows else None

    def inventory(self, shop_id: int | None = None) -> list[dict]:
        i = self.t["Inventory"]
        q = select(i.c.RationShopId, i.c.RationType, i.c.AvailableQuantity, i.c.MinimumStockLevel)
        if shop_id is not None:
            q = q.where(i.c.RationShopId == shop_id)
        return [
            {"shop_id": r["RationShopId"], "ration_type": r["RationType"],
             "available": as_float(r["AvailableQuantity"]), "reorder_level": as_float(r["MinimumStockLevel"])}
            for r in self._fetch(q)
        ]

    def movements(self, since: datetime, shop_id: int | None = None) -> list[dict]:
        if not self.has_table("InventoryMovements"):
            return []
        m = self.t["InventoryMovements"]
        q = select(m.c.Id, m.c.RationShopId, m.c.RationType, m.c.MovementType, m.c.Quantity,
                   m.c.BalanceAfter, m.c.CreatedAt).where(m.c.CreatedAt >= self._p(since))
        if shop_id is not None:
            q = q.where(m.c.RationShopId == shop_id)
        return [
            {"id": r["Id"], "shop_id": r["RationShopId"], "ration_type": r["RationType"], "type": r["MovementType"],
             "quantity": as_float(r["Quantity"]), "balance_after": as_float(r["BalanceAfter"]),
             "at": as_datetime(r["CreatedAt"])}
            for r in self._fetch(q.order_by(m.c.Id))
        ]

    def tokens(self, slot_from: date, slot_to: date, shop_id: int | None = None) -> list[dict]:
        """Tokens whose slot date is within [slot_from, slot_to], with slot times."""
        tk, ts = self.t["Tokens"], self.t["TimeSlots"]
        q = (
            select(tk.c.Id, tk.c.UserId, tk.c.RationShopId, tk.c.Status, tk.c.CreatedAt, tk.c.CollectedAt,
                   ts.c.SlotDate, ts.c.StartTime, ts.c.EndTime)
            .select_from(tk.join(ts, tk.c.TimeSlotId == ts.c.Id))
            .where(and_(ts.c.SlotDate >= self._p(datetime.combine(slot_from, datetime.min.time())),
                        ts.c.SlotDate < self._p(datetime.combine(slot_to, datetime.min.time()) + timedelta(days=1))))
        )
        if shop_id is not None:
            q = q.where(tk.c.RationShopId == shop_id)
        return [
            {"id": r["Id"], "user_id": r["UserId"], "shop_id": r["RationShopId"], "status": r["Status"],
             "created_at": as_datetime(r["CreatedAt"]), "collected_at": as_datetime(r["CollectedAt"]),
             "slot_date": as_date(r["SlotDate"]), "start": as_time(r["StartTime"]), "end": as_time(r["EndTime"])}
            for r in self._fetch(q)
        ]

    def booked_items_collected(self, since: datetime, shop_id: int | None = None) -> dict[tuple, float]:
        """Quantities booked on tokens completed since `since`, keyed by (shop, item)."""
        tk, ti = self.t["Tokens"], self.t["TokenItems"]
        q = (
            select(tk.c.RationShopId, ti.c.RationType, ti.c.Quantity)
            .select_from(ti.join(tk, ti.c.TokenId == tk.c.Id))
            .where(and_(tk.c.Status == 3, tk.c.CollectedAt >= self._p(since)))
        )
        if shop_id is not None:
            q = q.where(tk.c.RationShopId == shop_id)
        totals: dict[tuple, float] = {}
        for r in self._fetch(q):
            key = (r["RationShopId"], r["RationType"])
            totals[key] = totals.get(key, 0.0) + as_float(r["Quantity"])
        return totals

    def reserved_items(self, from_day: date, shop_id: int | None = None) -> list[dict]:
        """Items on confirmed/pending tokens not yet collected, slot today or later."""
        tk, ti, ts = self.t["Tokens"], self.t["TokenItems"], self.t["TimeSlots"]
        q = (
            select(tk.c.RationShopId, ti.c.RationType, ti.c.Quantity)
            .select_from(ti.join(tk, ti.c.TokenId == tk.c.Id).join(ts, tk.c.TimeSlotId == ts.c.Id))
            .where(and_(tk.c.Status.in_([1, 2]), ts.c.SlotDate >= self._p(datetime.combine(from_day, datetime.min.time()))))
        )
        if shop_id is not None:
            q = q.where(tk.c.RationShopId == shop_id)
        return [{"shop_id": r["RationShopId"], "ration_type": r["RationType"], "quantity": as_float(r["Quantity"])}
                for r in self._fetch(q)]

    def verification_events(self, since: datetime, shop_id: int | None = None) -> list[dict]:
        v = self.t["VerificationAuditLogs"]
        q = select(v.c.BeneficiaryId, v.c.ShopId, v.c.Action, v.c.Status, v.c.Reason, v.c.Timestamp).where(v.c.Timestamp >= self._p(since))
        if shop_id is not None:
            q = q.where(v.c.ShopId == shop_id)
        return [{"beneficiary_id": r["BeneficiaryId"], "shop_id": r["ShopId"], "action": r["Action"],
                 "status": r["Status"], "reason": r["Reason"] or "", "at": as_datetime(r["Timestamp"])} for r in self._fetch(q)]

    def beneficiaries(self, ids: list[int]) -> list[dict]:
        """Non-sensitive beneficiary context: code, assigned shop, monthly entitlement."""
        if not ids:
            return []
        b, f, fm, se = self.t["Beneficiaries"], self.t["Families"], self.t["FamilyMembers"], self.t["SchemeEntitlementItems"]
        base = self._fetch(
            select(b.c.Id, b.c.BeneficiaryCode, b.c.UserId, b.c.FamilyId, f.c.RationShopId, f.c.RationSchemeId)
            .select_from(b.join(f, b.c.FamilyId == f.c.Id)).where(b.c.Id.in_(ids))
        )
        family_ids = list({r["FamilyId"] for r in base})
        scheme_ids = list({r["RationSchemeId"] for r in base})
        eligible = {r["FamilyId"]: r["n"] for r in self._fetch(
            select(fm.c.FamilyId, func.count().label("n")).where(and_(fm.c.FamilyId.in_(family_ids), fm.c.Eligibility == 1))
            .group_by(fm.c.FamilyId))} if family_ids else {}
        quotas: dict[int, dict[int, float]] = {}
        for r in self._fetch(select(se.c.RationSchemeId, se.c.RationType, se.c.QuotaPerEligibleMemberPerMonth)
                             .where(se.c.RationSchemeId.in_(scheme_ids))) if scheme_ids else []:
            quotas.setdefault(r["RationSchemeId"], {})[r["RationType"]] = as_float(r["QuotaPerEligibleMemberPerMonth"])
        return [
            {"id": r["Id"], "code": r["BeneficiaryCode"], "user_id": r["UserId"], "assigned_shop_id": r["RationShopId"],
             "monthly_entitlement": {rt: q * eligible.get(r["FamilyId"], 0) for rt, q in quotas.get(r["RationSchemeId"], {}).items()}}
            for r in base
        ]

    def beneficiary_ids_for_users(self, user_ids: list[int]) -> dict[int, int]:
        if not user_ids:
            return {}
        b = self.t["Beneficiaries"]
        return {r["UserId"]: r["Id"] for r in self._fetch(select(b.c.Id, b.c.UserId).where(b.c.UserId.in_(user_ids)))}
