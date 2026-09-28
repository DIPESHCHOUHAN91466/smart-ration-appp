"""Synthetic distribution history for development / demos (NOT real data).

Writes months of realistic, fully fictional history into the EXISTING Smart
Ration database (MySQL or SQLite) so forecasting, alerts and analytics have
something to learn from:

  households -> families -> members -> entitlement -> tokens -> time slots
  -> collections -> collection items -> inventory ledger (receipts, issues,
  damage) -> verification audit events

Guarantees (checked again by --verify after writing):
  * No successful collection exceeds the family's monthly entitlement or the
    per-visit cap (RationItems.StandardQuotaPerBooking).
  * Stock never goes negative: a visit that can't be fully served is rejected
    (logged as CollectionRejected), never partially or negatively issued.
  * Only active, eligible households collect; slots respect capacity (2).
  * The ledger chains correctly and ends at the shop's real balance.

Everything generated is marked (SR-HIST-/COL-HIST-/FAM-HIST-/BEN-HIST- codes,
DataSource=SYNTHETIC_HISTORY, HIST- references) so --replace can remove it.
Deterministic for a given --seed and database state.

Usage (from ai, with the venv):
    python scripts/generate_history.py --months 12 --seed 42
    python scripts/generate_history.py --months 12 --seed 42 --replace
    python scripts/generate_history.py --verify
Needs a WRITE-capable URL: SMARTRATION_WRITE_DB_URL in .env or --db-url.
The AI service's own read-only account cannot (and should not) run this.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import string
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, create_engine, delete, func, insert, select
from sqlalchemy.engine import Connection, Engine

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MARK = "SYNTHETIC_HISTORY"
SLOT_CAPACITY = 2
OPEN_MINUTE, CLOSE_MINUTE = 9 * 60, 17 * 60
BCRYPT_ALPHABET = "./" + string.ascii_uppercase + string.ascii_lowercase + string.digits

# Uptake by calendar month: lower in the monsoon, higher around Diwali.
SEASONALITY = {1: 1.0, 2: 0.97, 3: 0.95, 4: 0.93, 5: 0.92, 6: 0.9, 7: 0.84, 8: 0.87, 9: 0.95, 10: 1.1, 11: 1.12, 12: 1.0}

TOKEN_COMPLETED, TOKEN_CONFIRMED = 3, 2
RECEIVED, DISTRIBUTED, DAMAGED, ADJUSTMENT = 1, 2, 3, 4
ACTION_COLLECTION_REJECTED, ACTION_TOKEN_ALREADY_USED = 9, 10
FIRST_NAMES = ["Asha", "Ramesh", "Sunita", "Vijay", "Kavita", "Sanjay", "Meena", "Rajesh", "Pooja", "Anil",
               "Lata", "Suresh", "Rekha", "Mahesh", "Savita", "Ganesh", "Usha", "Prakash", "Nanda", "Dilip"]
SURNAMES = ["Patil", "Pawar", "Jadhav", "Shinde", "More", "Kale", "Wagh", "Bhosale", "Gaikwad", "Chavan"]


# --------------------------------------------------------------------- db helpers

class Db:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.sqlite = engine.dialect.name == "sqlite"
        md = MetaData()
        names = ["Users", "Families", "FamilyMembers", "Beneficiaries", "RationShops", "RationSchemes", "SchemeEntitlementItems",
                 "RationItems", "Inventory", "InventoryMovements", "TimeSlots", "Tokens", "TokenItems", "RationCollections",
                 "RationCollectionItems", "VerificationAuditLogs"]
        self.t = {n: Table(n, md, autoload_with=engine) for n in names}

    # EF Core's SQLite provider stores these as TEXT; MySQL uses native types.
    def dt(self, v: datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S") if self.sqlite else v

    def dec(self, v: Decimal):
        return f"{v:.2f}" if self.sqlite else v

    def tm(self, minutes: int):
        t = time(minutes // 60, minutes % 60)
        return t.strftime("%H:%M:%S") if self.sqlite else timedelta(minutes=minutes)

    def next_id(self, conn: Connection, table: str) -> int:
        return (conn.execute(select(func.max(self.t[table].c.Id))).scalar() or 0) + 1


def to_date(v) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return datetime.fromisoformat(str(v)[:19].replace("T", " ")).date()


def D(v) -> Decimal:
    return Decimal(str(v))


def q2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


# --------------------------------------------------------------------- model

@dataclass
class Household:
    beneficiary_id: int
    user_id: int
    family_id: int
    shop_id: int
    monthly: dict[int, Decimal]  # ration type -> monthly entitlement
    existing: bool               # pre-existing (seeded) beneficiary
    code: str


@dataclass
class Rows:
    users: list = field(default_factory=list)
    families: list = field(default_factory=list)
    members: list = field(default_factory=list)
    beneficiaries: list = field(default_factory=list)
    slots: list = field(default_factory=list)
    tokens: list = field(default_factory=list)
    token_items: list = field(default_factory=list)
    collections: list = field(default_factory=list)
    collection_items: list = field(default_factory=list)
    movements: list = field(default_factory=list)
    audits: list = field(default_factory=list)


class Generator:
    def __init__(self, db: Db, conn: Connection, months: int, seed: int, households_per_shop: int, today: date):
        self.db, self.conn, self.rng = db, conn, random.Random(seed)
        self.today = today
        self.households_per_shop = households_per_shop
        self.rows = Rows()
        self.ids = {t: db.next_id(conn, t) for t in ["Users", "Families", "FamilyMembers", "Beneficiaries", "TimeSlots",
                                                    "Tokens", "TokenItems", "RationCollections", "RationCollectionItems",
                                                    "InventoryMovements", "VerificationAuditLogs"]}
        self.counter = defaultdict(int)
        self.rejected = 0

        t = db.t
        self.shops = [r._mapping for r in conn.execute(select(t["RationShops"]).where(t["RationShops"].c.IsActive == True))]  # noqa: E712
        self.visit_cap = {r.RationType: D(r.StandardQuotaPerBooking) for r in conn.execute(select(t["RationItems"]).where(t["RationItems"].c.IsActive == True))}  # noqa: E712
        self.quotas = defaultdict(dict)
        for r in conn.execute(select(t["SchemeEntitlementItems"])):
            self.quotas[r.RationSchemeId][r.RationType] = D(r.QuotaPerEligibleMemberPerMonth)
        self.schemes = [r.Id for r in conn.execute(select(t["RationSchemes"].c.Id).order_by(t["RationSchemes"].c.Id))]
        self.inventory = {(r.RationShopId, r.RationType): r._mapping for r in conn.execute(select(t["Inventory"]))}
        self.operators = self._operators()

        # History ends the day before the earliest existing slot, so it never
        # overlaps seeded/live bookings; it starts `months` whole months back.
        first_slot = conn.execute(select(func.min(t["TimeSlots"].c.SlotDate))).scalar()
        self.end = (to_date(first_slot) if first_slot else today) - timedelta(days=1)
        start_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        for _ in range(months - 1):
            start_month = (start_month - timedelta(days=1)).replace(day=1)
        self.start = start_month
        # Existing beneficiaries get nothing in the current month (their live
        # entitlement for this month must stay untouched).
        self.existing_cutoff = today.replace(day=1) - timedelta(days=1)

    def _operators(self) -> dict[int, int]:
        u = self.db.t["Users"]
        owners = {r.RationShopId: r.Id for r in self.conn.execute(select(u.c.Id, u.c.RationShopId).where(u.c.Role == 2)) if r.RationShopId}
        fallback = self.conn.execute(select(func.min(u.c.Id)).where(u.c.Role.in_([2, 3, 4]))).scalar() or 1
        return defaultdict(lambda: fallback, owners)

    def nid(self, table: str) -> int:
        value = self.ids[table]
        self.ids[table] += 1
        return value

    # ---------------------------------------------------------------- households

    def households(self) -> list[Household]:
        t = self.db.t
        eligible = defaultdict(int)
        for r in self.conn.execute(select(t["FamilyMembers"].c.FamilyId).where(t["FamilyMembers"].c.Eligibility == 1)):
            eligible[r.FamilyId] += 1
        result = []
        q = (select(t["Beneficiaries"].c.Id, t["Beneficiaries"].c.UserId, t["Beneficiaries"].c.FamilyId, t["Beneficiaries"].c.BeneficiaryCode,
                    t["Families"].c.RationShopId, t["Families"].c.RationSchemeId)
             .select_from(t["Beneficiaries"].join(t["Families"], t["Beneficiaries"].c.FamilyId == t["Families"].c.Id))
             .where(t["Beneficiaries"].c.IsActive == True, t["Beneficiaries"].c.IsBlocked == False))  # noqa: E712
        for r in self.conn.execute(q):
            members = eligible.get(r.FamilyId, 0)
            if members:
                monthly = {rt: q * members for rt, q in self.quotas[r.RationSchemeId].items()}
                result.append(Household(r.Id, r.UserId, r.FamilyId, r.RationShopId, monthly, not r.BeneficiaryCode.startswith("BEN-HIST-"), r.BeneficiaryCode))
        return result + self._create_households()

    def _create_households(self) -> list[Household]:
        u = self.db.t["Users"]
        used_mobiles = {r.MobileNumber for r in self.conn.execute(select(u.c.MobileNumber))}
        mobile = 8_100_000_000
        created = []
        now = datetime.combine(self.start, time(8, 0))
        for shop in self.shops:
            for _ in range(self.households_per_shop):
                self.counter["households"] += 1
                seq = self.counter["households"]
                while str(mobile) in used_mobiles:
                    mobile += 1
                user_id, family_id, ben_id = self.nid("Users"), self.nid("Families"), self.nid("Beneficiaries")
                scheme = self.schemes[0] if self.rng.random() < 0.8 or len(self.schemes) == 1 else self.schemes[1]
                size = self.rng.choice([2, 3, 3, 4, 4, 4, 5, 6])
                surname = self.rng.choice(SURNAMES)
                head = f"{self.rng.choice(FIRST_NAMES)} {surname}"
                # Structurally valid bcrypt hash that no password matches: these
                # accounts exist for history only and can never log in.
                pw = "$2a$11$" + "".join(self.rng.choice(BCRYPT_ALPHABET) for _ in range(53))
                self.rows.users.append(dict(Id=user_id, FullName=head, Email=f"hist{seq:05d}@history.synthetic.invalid",
                                            MobileNumber=str(mobile), PasswordHash=pw, Role=1, IsActive=True, CreatedAt=self.db.dt(now)))
                mobile += 1
                self.rows.families.append(dict(Id=family_id, FamilyCode=f"FAM-HIST-{seq:05d}", RationShopId=shop["Id"],
                                               RationSchemeId=scheme, DataSource=MARK, CreatedAt=self.db.dt(now)))
                eligible = 0
                for m in range(size):
                    relation = 1 if m == 0 else self.rng.choice([2, 3, 4, 5])
                    status = 1 if m == 0 or self.rng.random() < 0.92 else 4
                    eligible += status == 1
                    self.rows.members.append(dict(Id=self.nid("FamilyMembers"), FamilyId=family_id,
                                                  FullName=head if m == 0 else f"{self.rng.choice(FIRST_NAMES)} {surname}",
                                                  Age=self.rng.randint(25, 70) if m == 0 else self.rng.randint(1, 80),
                                                  Relationship=relation, Eligibility=status, DataSource=MARK))
                self.rows.beneficiaries.append(dict(
                    Id=ben_id, BeneficiaryCode=f"BEN-HIST-{seq:05d}", Address=f"Synthetic village address {seq}", UserId=user_id,
                    FamilyId=family_id, IsActive=True, IsBlocked=False, DataSource=MARK, CreatedAt=self.db.dt(now),
                    DateOfBirth=self.db.dt(datetime(self.rng.randint(1950, 2000), self.rng.randint(1, 12), self.rng.randint(1, 28))),
                    District=shop.get("District") or "Nagpur", Gender=self.rng.choice([1, 2]), Pincode="441001",
                    ProfilePhotoUrl=None, State=shop.get("State") or "Maharashtra", Village=shop.get("Village") or "Synthetic"))
                monthly = {rt: q * eligible for rt, q in self.quotas[scheme].items()}
                created.append(Household(ben_id, user_id, family_id, shop["Id"], monthly, False, f"BEN-HIST-{seq:05d}"))
        return created

    # ---------------------------------------------------------------- simulation

    def open_days(self, month_start: date) -> list[date]:
        days, d = [], month_start
        while d.month == month_start.month and d <= self.end:
            if d >= self.start and d.weekday() != 6:  # closed on Sundays
                days.append(d)
            d += timedelta(days=1)
        return days

    def plan_visits(self, households: list[Household]) -> dict[date, list[tuple[Household, int]]]:
        """Each household's visits per month: enough visits to take its
        entitlement given the per-visit cap, thinned by seasonal uptake."""
        plan = defaultdict(list)
        month = self.start
        festival_shop = self.shops[min(2, len(self.shops) - 1)]["Id"] if self.shops else None
        while month <= self.end:
            days = self.open_days(month)
            early = days[: max(1, math.ceil(len(days) * 0.75))]  # uptake concentrates early in the cycle
            uptake = SEASONALITY[month.month]
            for h in households:
                if h.existing and month > self.existing_cutoff:
                    continue
                needed = max((math.ceil(ent / self.visit_cap[rt]) for rt, ent in h.monthly.items() if ent > 0 and self.visit_cap.get(rt)), default=0)
                visits = sum(1 for _ in range(needed) if self.rng.random() < min(0.97, 0.82 * uptake))
                if not days or visits == 0:
                    continue
                for day in self._spread(early, visits):
                    plan[day].append((h, month.month))
            # Controlled anomaly 1: one-day distribution camp at one shop in
            # festival season (a real, legitimate demand spike).
            if month.month == 10 and festival_shop and days:
                camp = days[min(9, len(days) - 1)]
                extra = [h for h in households if h.shop_id == festival_shop and not (h.existing and month > self.existing_cutoff)]
                plan[camp].extend((h, month.month) for h in self.rng.sample(extra, min(len(extra), 12)))
            month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
        return plan

    def _spread(self, pool: list[date], visits: int) -> list[date]:
        """One visit per equal segment of the collection window, at most one
        visit per ~4 open days: households don't return the next day."""
        visits = min(visits, max(1, len(pool) // 4))
        seg = len(pool) / visits
        return [pool[min(len(pool) - 1, int(k * seg + self.rng.random() * seg * 0.5))] for k in range(visits)]

    def run(self, households: list[Household]) -> None:
        plan = self.plan_visits(households)
        shop_ids = [s["Id"] for s in self.shops]
        # Stock simulation per shop x item.
        balance: dict[tuple, Decimal] = {}
        pending_delivery: dict[tuple, tuple[date, Decimal]] = {}
        target: dict[tuple, Decimal] = {}
        for key, inv in self.inventory.items():
            reorder = max(D(inv["MinimumStockLevel"]), D(20))
            target[key] = q2(reorder * 4)
            balance[key] = q2(reorder * 3)
            self._move(key, RECEIVED, balance[key], balance[key], datetime.combine(self.start, time(7, 0)), "HIST-OPENING", "Synthetic opening stock")
        delayed_shop = shop_ids[min(1, len(shop_ids) - 1)] if shop_ids else None
        damage_shop = shop_ids[min(3, len(shop_ids) - 1)] if shop_ids else None
        damage_window_start = self.end - timedelta(days=20)

        taken: dict[tuple, Decimal] = defaultdict(Decimal)  # (household, year, month, type) -> qty
        day = self.start
        while day <= self.end:
            # Morning deliveries.
            for key, (arrive, qty) in list(pending_delivery.items()):
                if arrive <= day:
                    balance[key] += qty
                    self._move(key, RECEIVED, qty, balance[key], datetime.combine(day, time(8, 0)), f"HIST-DEL-{day:%Y%m%d}", "Synthetic delivery")
                    del pending_delivery[key]

            if day.weekday() != 6:
                for shop_id in shop_ids:
                    visitors = [(h, m) for h, m in plan.get(day, []) if h.shop_id == shop_id]
                    self._serve_day(shop_id, day, visitors, balance, taken)

            # Evening write-offs (after the day's issues, matching their 18:00 timestamp): a small monthly one everywhere (25th). Controlled
            # anomaly 2: heavier weekly write-offs at one shop in the last weeks.
            heavy = damage_shop is not None and day >= damage_window_start and day.weekday() == 5
            if day.day == 25 or heavy:
                for key in list(balance):
                    is_heavy = heavy and key[0] == damage_shop
                    if day.day != 25 and not is_heavy:
                        continue
                    qty = q2(balance[key] * (Decimal("0.02") if is_heavy else Decimal("0.004")))
                    if qty > 0:
                        balance[key] -= qty
                        self._move(key, DAMAGED, qty, balance[key], datetime.combine(day, time(18, 0)), f"HIST-DMG-{day:%Y%m%d}", "Synthetic damage write-off")

            # Reorder when stock falls to the reorder level. Controlled anomaly 3:
            # one shop's supplies arrive late in the second-to-last month.
            for key, bal in balance.items():
                inv = self.inventory[key]
                if key not in pending_delivery and bal <= max(D(inv["MinimumStockLevel"]), D(20)):
                    lead = self.rng.randint(2, 5)
                    if key[0] == delayed_shop and (self.end - day).days in range(25, 60):
                        lead += 30  # long enough to run dry: a genuine low-stock period
                    pending_delivery[key] = (day + timedelta(days=lead), q2(target[key] - bal))
            day += timedelta(days=1)

        self._reconcile(balance)
        self._token_reuse_attempts(households)

    def _serve_day(self, shop_id, day, visitors, balance, taken):
        if not visitors:
            return
        self.rng.shuffle(visitors)
        minute = OPEN_MINUTE + self.rng.randint(0, 20)
        slot_load: dict[int, int] = defaultdict(int)
        slot_ids: dict[int, int] = {}
        operator = self.operators[shop_id]
        for h, _month in visitors:
            # Busy counter: 3-7 minutes between people, occasional idle gaps.
            minute += self.rng.randint(3, 7) if self.rng.random() > 0.08 else self.rng.randint(20, 50)
            slot = (minute // 5) * 5
            while slot < CLOSE_MINUTE and slot_load[slot] >= SLOT_CAPACITY:
                slot += 5
            if slot >= CLOSE_MINUTE:
                break  # shop closed for the day; remaining visitors don't come
            slot_load[slot] += 1
            minute = max(minute, slot)

            request = {}
            for rt, monthly in h.monthly.items():
                remaining = monthly - taken[(h.beneficiary_id, day.year, day.month, rt)]
                qty = q2(min(remaining, self.visit_cap.get(rt, Decimal(0))))
                if qty > 0:
                    request[rt] = qty
            if not request:
                slot_load[slot] -= 1
                continue

            if slot not in slot_ids:
                slot_ids[slot] = self.nid("TimeSlots")
                self.rows.slots.append(dict(Id=slot_ids[slot], RationShopId=shop_id, SlotDate=self.db.dt(datetime.combine(day, time())),
                                            StartTime=self.db.tm(slot), EndTime=self.db.tm(slot + 5), Capacity=SLOT_CAPACITY, BookedCount=0))
            slot_row = next(s for s in reversed(self.rows.slots) if s["Id"] == slot_ids[slot])
            slot_row["BookedCount"] += 1

            self.counter["tokens"] += 1
            token_id = self.nid("Tokens")
            token_number = f"SR-HIST-{self.counter['tokens']:06d}"
            booked_at = datetime.combine(day - timedelta(days=self.rng.randint(1, 4)), time(self.rng.randint(8, 20), self.rng.randint(0, 59)))
            # Seconds-level jitter only: people are served in order, so times strictly increase.
            at = datetime.combine(day, time()) + timedelta(minutes=minute, seconds=self.rng.randint(0, 59))
            in_stock = all(balance.get((shop_id, rt), Decimal(0)) >= qty for rt, qty in request.items())

            self.rows.tokens.append(dict(Id=token_id, TokenNumber=token_number, UserId=h.user_id, RationShopId=shop_id, TimeSlotId=slot_ids[slot],
                                         Status=TOKEN_COMPLETED if in_stock else TOKEN_CONFIRMED, QRCodeValue=None,
                                         CreatedAt=self.db.dt(booked_at), CollectedAt=self.db.dt(at) if in_stock else None))
            for rt, qty in request.items():
                self.rows.token_items.append(dict(Id=self.nid("TokenItems"), TokenId=token_id, RationType=rt, Quantity=self.db.dec(qty)))

            if not in_stock:
                # All-or-nothing, like the live system: rejected, nothing issued.
                self.rejected += 1
                self._audit(ACTION_COLLECTION_REJECTED, "BLOCKED", h.beneficiary_id, shop_id, token_number, at, "Insufficient shop inventory.")
                continue

            self.counter["collections"] += 1
            collection_id = self.nid("RationCollections")
            self.rows.collections.append(dict(Id=collection_id, CollectionCode=f"COL-HIST-{self.counter['collections']:06d}", TokenId=token_id,
                                              BeneficiaryId=h.beneficiary_id, RationShopId=shop_id, OperatorUserId=operator,
                                              VerificationMethod="QR" if self.rng.random() < 0.9 else "OTP", CollectedAt=self.db.dt(at), IdempotencyKey=None))
            for rt, qty in request.items():
                key = (shop_id, rt)
                balance[key] -= qty
                taken[(h.beneficiary_id, day.year, day.month, rt)] += qty
                self.rows.collection_items.append(dict(Id=self.nid("RationCollectionItems"), RationCollectionId=collection_id,
                                                       RationType=rt, Quantity=self.db.dec(qty)))
                self._move(key, DISTRIBUTED, qty, balance[key], at, token_number, None)

    def _reconcile(self, balance):
        """Close the synthetic ledger at the balance the live ledger (or the
        current Inventory row) starts from, with a visible Adjustment."""
        m = self.db.t["InventoryMovements"]
        first_live = {}
        for r in self.conn.execute(select(m).order_by(m.c.CreatedAt, m.c.Id)):
            key = (r.RationShopId, r.RationType)
            if key not in first_live:
                signed = D(r.Quantity) if r.MovementType in (RECEIVED, ADJUSTMENT) else -D(r.Quantity)
                first_live[key] = D(r.BalanceAfter) - signed
        at = datetime.combine(self.end, time(23, 0))
        for key, bal in balance.items():
            goal = q2(first_live.get(key, D(self.inventory[key]["AvailableQuantity"])))
            if goal != bal:
                self._move(key, ADJUSTMENT, goal - bal, goal, at, "HIST-RECON", "Reconciliation to the recorded balance at the end of imported history")

    def _token_reuse_attempts(self, households):
        """Controlled anomaly 4: a few blocked attempts to reuse collected tokens."""
        done = [t for t in self.rows.tokens if t["Status"] == TOKEN_COMPLETED]
        by_user = {h.user_id: h for h in households}
        for t in self.rng.sample(done, min(3, len(done))):
            h = by_user[t["UserId"]]
            at = datetime.fromisoformat(str(t["CollectedAt"])) + timedelta(days=2)
            for _ in range(2):
                self._audit(ACTION_TOKEN_ALREADY_USED, "BLOCKED", h.beneficiary_id, t["RationShopId"], t["TokenNumber"], at,
                            "This token has already been used for collection.")

    def _move(self, key, mtype, qty, balance_after, at, reference, note):
        self.rows.movements.append(dict(Id=self.nid("InventoryMovements"), RationShopId=key[0], RationType=key[1], MovementType=mtype,
                                        Quantity=self.db.dec(qty), BalanceAfter=self.db.dec(balance_after), Reference=reference, Note=note,
                                        RecordedByUserId=None, CreatedAt=self.db.dt(at)))

    def _audit(self, action, status, beneficiary_id, shop_id, token_number, at, reason):
        self.rows.audits.append(dict(Id=self.nid("VerificationAuditLogs"), VerificationReference=f"HIST-{token_number}", TokenNumber=token_number,
                                     BeneficiaryId=beneficiary_id, ShopId=shop_id, Action=action, VerificationMethod="QR", Status=status,
                                     Reason=reason, OperatorId=None, DeviceInfo=MARK, IpAddress=None, Timestamp=self.db.dt(at)))


# --------------------------------------------------------------------- write / replace / verify

ORDER = [("Users", "users"), ("Families", "families"), ("FamilyMembers", "members"), ("Beneficiaries", "beneficiaries"),
         ("TimeSlots", "slots"), ("Tokens", "tokens"), ("TokenItems", "token_items"), ("RationCollections", "collections"),
         ("RationCollectionItems", "collection_items"), ("InventoryMovements", "movements"), ("VerificationAuditLogs", "audits")]


def write(db: Db, conn: Connection, rows: Rows, batch: int = 2000) -> dict[str, int]:
    counts = {}
    for table, attr in ORDER:
        data = getattr(rows, attr)
        for i in range(0, len(data), batch):
            conn.execute(insert(db.t[table]), data[i:i + batch])
        counts[table] = len(data)
    return counts


def existing_history(db: Db, conn: Connection) -> int:
    t = db.t["Tokens"]
    return conn.execute(select(func.count()).select_from(t).where(t.c.TokenNumber.like("SR-HIST-%"))).scalar() or 0


def remove_history(db: Db, conn: Connection) -> None:
    t = db.t
    tokens = select(t["Tokens"].c.Id).where(t["Tokens"].c.TokenNumber.like("SR-HIST-%"))
    slot_ids = [r[0] for r in conn.execute(select(t["Tokens"].c.TimeSlotId).where(t["Tokens"].c.TokenNumber.like("SR-HIST-%")).distinct())]
    collections = select(t["RationCollections"].c.Id).where(t["RationCollections"].c.CollectionCode.like("COL-HIST-%"))
    conn.execute(delete(t["RationCollectionItems"]).where(t["RationCollectionItems"].c.RationCollectionId.in_(collections)))
    conn.execute(delete(t["RationCollections"]).where(t["RationCollections"].c.CollectionCode.like("COL-HIST-%")))
    conn.execute(delete(t["TokenItems"]).where(t["TokenItems"].c.TokenId.in_(tokens)))
    conn.execute(delete(t["Tokens"]).where(t["Tokens"].c.TokenNumber.like("SR-HIST-%")))
    for i in range(0, len(slot_ids), 1000):
        chunk = slot_ids[i:i + 1000]
        still_used = select(t["Tokens"].c.TimeSlotId).where(t["Tokens"].c.TimeSlotId.in_(chunk))
        conn.execute(delete(t["TimeSlots"]).where(t["TimeSlots"].c.Id.in_(chunk), ~t["TimeSlots"].c.Id.in_(still_used)))
    m = t["InventoryMovements"]
    conn.execute(delete(m).where(m.c.Reference.like("HIST-%") | m.c.Reference.like("SR-HIST-%")))
    v = t["VerificationAuditLogs"]
    conn.execute(delete(v).where(v.c.VerificationReference.like("HIST-%")))
    fam = select(t["Families"].c.Id).where(t["Families"].c.DataSource == MARK)
    users = select(t["Beneficiaries"].c.UserId).where(t["Beneficiaries"].c.DataSource == MARK)
    user_ids = [r[0] for r in conn.execute(users)]
    conn.execute(delete(t["Beneficiaries"]).where(t["Beneficiaries"].c.DataSource == MARK))
    conn.execute(delete(t["FamilyMembers"]).where(t["FamilyMembers"].c.FamilyId.in_(fam)))
    conn.execute(delete(t["Families"]).where(t["Families"].c.DataSource == MARK))
    for i in range(0, len(user_ids), 1000):
        conn.execute(delete(t["Users"]).where(t["Users"].c.Id.in_(user_ids[i:i + 1000])))


def verify(db: Db, conn: Connection) -> list[str]:
    """Independent re-check of the generated data's invariants."""
    t, problems = db.t, []
    eligible = defaultdict(int)
    for r in conn.execute(select(t["FamilyMembers"].c.FamilyId).where(t["FamilyMembers"].c.Eligibility == 1)):
        eligible[r.FamilyId] += 1
    quotas = defaultdict(dict)
    for r in conn.execute(select(t["SchemeEntitlementItems"])):
        quotas[r.RationSchemeId][r.RationType] = D(r.QuotaPerEligibleMemberPerMonth)
    caps = {r.RationType: D(r.StandardQuotaPerBooking) for r in conn.execute(select(t["RationItems"]))}
    families = {r.Id: r for r in conn.execute(select(t["Families"]))}
    ben_family = {r.Id: r.FamilyId for r in conn.execute(select(t["Beneficiaries"].c.Id, t["Beneficiaries"].c.FamilyId))}

    c, ci = t["RationCollections"], t["RationCollectionItems"]
    monthly = defaultdict(Decimal)
    for r in conn.execute(select(c.c.BeneficiaryId, c.c.CollectedAt, ci.c.RationType, ci.c.Quantity)
                          .select_from(ci.join(c, ci.c.RationCollectionId == c.c.Id)).where(c.c.CollectionCode.like("COL-HIST-%"))):
        qty = D(r.Quantity)
        if qty <= 0 or qty > caps.get(r.RationType, Decimal(0)):
            problems.append(f"per-visit cap violated: beneficiary {r.BeneficiaryId} {r.RationType} {qty}")
        at = to_date(r.CollectedAt)
        monthly[(ben_family[r.BeneficiaryId], at.year, at.month, r.RationType)] += qty
    for (fid, _, _, rt), qty in monthly.items():
        fam = families[fid]
        allowed = quotas[fam.RationSchemeId].get(rt, Decimal(0)) * eligible[fid]
        if qty > allowed:
            problems.append(f"entitlement exceeded: family {fid} type {rt} {qty} > {allowed}")

    m = t["InventoryMovements"]
    last = {}
    for r in conn.execute(select(m).order_by(m.c.CreatedAt, m.c.Id)):
        key = (r.RationShopId, r.RationType)
        bal = D(r.BalanceAfter)
        if bal < 0:
            problems.append(f"negative stock at movement {r.Id}")
        signed = D(r.Quantity) if r.MovementType in (RECEIVED, ADJUSTMENT) else -D(r.Quantity)
        if key in last and abs(last[key] + signed - bal) > Decimal("0.01"):
            problems.append(f"ledger chain break at movement {r.Id}")
        last[key] = bal
    for r in conn.execute(select(t["Inventory"])):
        key = (r.RationShopId, r.RationType)
        if key in last and abs(last[key] - D(r.AvailableQuantity)) > Decimal("0.01"):
            problems.append(f"ledger end {last[key]} != inventory {r.AvailableQuantity} for {key}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--months", type=int, default=12, help="whole months of history (1-24)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--households-per-shop", type=int, default=20, help="extra synthetic households per shop")
    ap.add_argument("--db-url", default=os.getenv("SMARTRATION_WRITE_DB_URL", ""))
    ap.add_argument("--replace", action="store_true", help="delete previously generated history first")
    ap.add_argument("--dry-run", action="store_true", help="simulate and report counts without writing")
    ap.add_argument("--verify", action="store_true", help="only check invariants of existing generated data")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD), for tests")
    args = ap.parse_args(argv)

    if not args.db_url:
        print("No database URL. Set SMARTRATION_WRITE_DB_URL in ai/.env or pass --db-url.", file=sys.stderr)
        return 2
    if not 1 <= args.months <= 24 or not 0 <= args.households_per_shop <= 500:
        print("--months must be 1-24 and --households-per-shop 0-500.", file=sys.stderr)
        return 2

    engine = create_engine(args.db_url, future=True)
    db = Db(engine)
    today = date.fromisoformat(args.today) if args.today else date.today()

    if args.verify:
        with engine.connect() as conn:
            problems = verify(db, conn)
        print("OK: no invariant violations." if not problems else "\n".join(["VIOLATIONS:"] + problems[:50]))
        return 0 if not problems else 1

    with engine.begin() as conn:  # one transaction: all or nothing
        if existing_history(db, conn):
            if not args.replace:
                print("Generated history already exists. Re-run with --replace to regenerate it.", file=sys.stderr)
                return 3
            remove_history(db, conn)
        gen = Generator(db, conn, args.months, args.seed, args.households_per_shop, today)
        if gen.end < gen.start:
            print("Nothing to generate: the history window is empty.", file=sys.stderr)
            return 2
        households = gen.households()
        gen.run(households)
        summary = {name: len(getattr(gen.rows, attr)) for name, attr in ORDER}
        if args.dry_run:
            conn.rollback()
        else:
            write(db, conn, gen.rows)
            problems = verify(db, conn)
            if problems:
                raise SystemExit("Generated data failed verification (rolled back):\n" + "\n".join(problems[:20]))

    mode = "DRY RUN (nothing written)" if args.dry_run else "Written"
    print(f"{mode}: {gen.start} .. {gen.end} ({args.months} months, seed {args.seed}), {len(households)} households, "
          f"{gen.rejected} visits rejected for lack of stock.")
    for table, n in summary.items():
        print(f"  {table:<24}{n:>8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
