"""Official date-range reports count Indian calendar days (2026-10-17, Phase 3 Q1).

/api/admin/statistics and /api/admin/reports take fromDate/toDate (calendar dates, both included). Until this change
the days were UTC days, so a token created at 01:30 IST was counted on the previous day. Synthetic rows below are
created at exact UTC instants; the expected Indian date is in each comment."""

from __future__ import annotations

from datetime import datetime

import pytest
from ration_world import session
from sqlalchemy import select

import app.utils.time as clock
from app.database.enums import TokenStatus
from app.database.models import AuditLog, Token, User
from app.services import government_service

CREATED = {
    "t1": datetime(2026, 10, 14, 18, 29),   # 14 Oct 23:59 IST
    "t2": datetime(2026, 10, 14, 18, 30),   # 15 Oct 00:00 IST (UTC date still the 14th)
    "t3": datetime(2026, 10, 15, 20, 0),    # 16 Oct 01:30 IST (UTC date still the 15th)
    "t4": datetime(2026, 10, 31, 18, 29),   # 31 Oct 23:59 IST
    "t5": datetime(2026, 10, 31, 19, 0),    # 1 Nov 00:30 IST (UTC date still 31 Oct)
}


@pytest.fixture
def tokens(env):
    with session() as db:
        user_id = db.scalar(select(User.Id).where(User.Email == "asha@example.com"))
        for n, (name, created) in enumerate(CREATED.items(), start=1):
            db.add(Token(TokenNumber=f"SR-2026-9{n:05d}", UserId=user_id, RationShopId=1, TimeSlotId=2,
                         Status=int(TokenStatus.Completed if name in ("t2", "t3") else TokenStatus.Confirmed), CreatedAt=created))
            if name in ("t2", "t3"):   # a completed collection is audited when it happens
                db.add(AuditLog(UserId=50, Action="COLLECTION_COMPLETED", EntityName="Token", EntityId=str(n), CreatedAt=created))
        db.commit()
    return env


def _stats(env, start: str, end: str) -> dict:
    r = env["client"].get("/api/admin/statistics", params={"fromDate": start, "toDate": end}, headers=env["official"])
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _reports(env, start: str, end: str) -> dict:
    r = env["client"].get("/api/admin/reports", params={"fromDate": start, "toDate": end}, headers=env["official"])
    assert r.status_code == 200, r.text
    return {row["reportName"]: row["recordCount"] for row in r.json()["data"]}


def test_a_single_indian_day_counts_from_ist_midnight_to_ist_midnight(tokens):
    assert _stats(tokens, "2026-10-15", "2026-10-15")["tokensGenerated"] == 1          # t2 only (UTC day would give t3)
    assert _stats(tokens, "2026-10-16", "2026-10-16")["tokensGenerated"] == 1          # t3, though its UTC date is the 15th
    assert _stats(tokens, "2026-10-14", "2026-10-14")["tokensGenerated"] == 1          # t1 (23:59 IST)


def test_the_end_date_is_included(tokens):
    stats = _stats(tokens, "2026-10-14", "2026-10-15")
    assert stats["tokensGenerated"] == 2 and stats["collectionsCompleted"] == 1      # t1 + t2
    assert stats["fromDate"].startswith("2026-10-14") and stats["toDate"].startswith("2026-10-15")   # echoed as before


def test_month_boundaries_follow_the_indian_calendar(tokens):
    assert _stats(tokens, "2026-10-01", "2026-10-31")["tokensGenerated"] == 4          # t1..t4; t5 is 1 Nov in India
    assert _stats(tokens, "2026-11-01", "2026-11-30")["tokensGenerated"] == 1          # t5


def test_an_empty_range_and_a_reversed_range(tokens):
    assert _stats(tokens, "2026-10-20", "2026-10-25")["tokensGenerated"] == 0
    assert _stats(tokens, "2026-10-15", "2026-10-14")["tokensGenerated"] == 2          # reversed ends are swapped, as before


def test_adjacent_ranges_never_count_an_event_twice(tokens):
    whole = _stats(tokens, "2026-10-14", "2026-11-01")["tokensGenerated"]
    parts = sum(_stats(tokens, a, b)["tokensGenerated"] for a, b in
                (("2026-10-14", "2026-10-14"), ("2026-10-15", "2026-10-31"), ("2026-11-01", "2026-11-01")))
    assert whole == parts == 5


def test_the_reports_page_uses_the_same_days(tokens):
    day16 = _reports(tokens, "2026-10-16", "2026-10-16")
    assert day16["Token Generation Report"] == 1 and day16["Daily Collection Report"] == 1
    assert day16["QR Verification Report"] == 1                                         # the audit row at 01:30 IST
    assert _reports(tokens, "2026-10-15", "2026-10-15")["QR Verification Report"] == 1   # the one at 00:00 IST


def test_without_dates_the_range_ends_today_in_india(tokens, monkeypatch):
    for module in (clock, government_service):
        monkeypatch.setattr(module, "utc_now", lambda: datetime(2026, 10, 15, 20, 0), raising=False)   # 16 Oct 01:30 IST
    data = tokens["client"].get("/api/admin/statistics", headers=tokens["official"]).json()["data"]
    assert data["toDate"].startswith("2026-10-16") and data["fromDate"].startswith("2026-09-17")
