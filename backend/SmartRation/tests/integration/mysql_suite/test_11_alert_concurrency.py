"""AI-alert refreshes on real MySQL from two application instances (2026-10-17, Phase 5).

Rule alerts are detected on every official visit to the intelligence centre, and AI-service alerts on every sync. Both
check for an open alert and insert one if none exists; without coordination, two refreshes at the same moment both
see "none" and both insert (plus a second notification to the shop owner). The protection under test: a MySQL named
lock (GET_LOCK) taken on its own connection around the check-then-insert, and a fresh read snapshot once it is held.
Runs only against a *_test database (see conftest.py)."""

from __future__ import annotations

import logging
from datetime import timedelta

import pytest
from sqlalchemy import func, select, text

from app.api.dependencies.auth import Actor
from app.database.enums import AIAlertStatus, UserRole, VerificationAction
from app.database.models import AIAlert, Notification, RationShop, User, VerificationAuditLog
from app.services import ai_alert_service, ai_rules_service
from app.services.ai_client import AiResult
from app.utils.time import utc_now
from mysql_suite.support import new_session
from mysql_suite.test_10_collection_concurrency import run_parallel

REFRESHES = 8


@pytest.fixture
def two_instances(engine, test_url):
    from sqlalchemy.orm import sessionmaker

    from app.database.connection import _build_engine
    second = _build_engine(test_url)
    other = sessionmaker(bind=second, autoflush=False, expire_on_commit=False)
    yield lambda i: new_session() if i % 2 == 0 else other()   # even workers on instance A, odd on instance B
    second.dispose()


def _log(db, action: VerificationAction, beneficiary_id: int, shop_id: int | None = None, token: str | None = None,
         status: str = "SUCCESS") -> None:
    db.add(VerificationAuditLog(Action=int(action), BeneficiaryId=beneficiary_id, ShopId=shop_id, TokenNumber=token,
                                VerificationMethod="QR", Status=status, Timestamp=utc_now() - timedelta(minutes=5)))


@pytest.fixture
def suspicious(db, password_hash):
    """Three separate events in the last 24 hours: repeated QR scans for two (synthetic) beneficiaries, and repeated
    rejected collections on one token at a shop that has an owner (so that alert also notifies them)."""
    shop_id = db.scalar(select(RationShop.Id).order_by(RationShop.Id).limit(1))
    owner = User(FullName="Alert Shop", Email="alert-owner@example.test", MobileNumber="7000000201", PasswordHash=password_hash,
                 Role=int(UserRole.ShopOwner), RationShopId=shop_id, IsActive=True, CreatedAt=utc_now())
    official = User(FullName="Alert Official", Email="alert-official@example.test", MobileNumber="7000000202",
                    PasswordHash=password_hash, Role=int(UserRole.GovernmentOfficial), IsActive=True, CreatedAt=utc_now())
    db.add_all([owner, official])
    for _ in range(4):
        _log(db, VerificationAction.QrScanned, 9001)
        _log(db, VerificationAction.QrScanned, 9002)
    for _ in range(2):
        _log(db, VerificationAction.CollectionRejected, 9003, shop_id, "TKN-RACE-1", "BLOCKED")
    db.commit()
    return {"shop_id": shop_id, "owner_id": owner.Id,
            "official": Actor(user_id=official.Id, role=UserRole.GovernmentOfficial, ration_shop_id=None)}


def _alerts(db) -> list[tuple]:
    db.rollback()   # end this session's REPEATABLE-READ snapshot so the workers' commits are visible
    return sorted(db.execute(select(AIAlert.AlertType, AIAlert.ShopId, AIAlert.BeneficiaryId, AIAlert.Severity)).tuples().all(),
                  key=repr)


def _notifications(db, user_id: int) -> int:
    db.rollback()
    return db.scalar(select(func.count()).select_from(Notification).where(Notification.UserId == user_id)) or 0


EXPECTED_RULE_ALERTS = [("DuplicateCollectionAttempt", "shop", 9003, 3), ("RepeatedQrScan", None, 9001, 2),
                        ("RepeatedQrScan", None, 9002, 2)]


def _expected(world) -> list[tuple]:
    return sorted([(t, world["shop_id"] if s == "shop" else None, b, sev) for t, s, b, sev in EXPECTED_RULE_ALERTS], key=repr)


def _scan(session_factory):
    with session_factory() as s:
        s.scalar(select(func.count()).select_from(AIAlert))   # like the sign-in check: this request's snapshot starts here
        return ai_rules_service.scan_and_detect(s)


# ---------------------------------------------------------------- rule alerts (intelligence centre)

def test_rule_alerts_refreshed_by_many_officials_on_two_instances_are_created_once(db, suspicious, two_instances):
    results = run_parallel(lambda i: _scan(lambda: two_instances(i)), REFRESHES)

    assert [r for r in results if isinstance(r, Exception)] == []
    assert sum(len(r) for r in results) == 3                         # each event created by exactly one refresh
    assert _alerts(db) == _expected(suspicious)                      # different events: all three, each once
    assert _notifications(db, suspicious["owner_id"]) == 1           # the shop owner is told once


def test_a_later_refresh_after_a_concurrent_one_adds_nothing(db, suspicious, two_instances):
    run_parallel(lambda i: _scan(lambda: two_instances(i)), REFRESHES)
    assert _scan(new_session) == []
    assert len(_alerts(db)) == 3 and _notifications(db, suspicious["owner_id"]) == 1


# ---------------------------------------------------------------- AI-service alerts (sync)

class FakeAi:
    """Stands in for the optional AI service: the same three candidates on every call."""

    ITEMS = [{"dedup_key": "stock:race:1", "alert_type": "StockoutRisk", "severity": "High", "description": "a"},
             {"dedup_key": "stock:race:2", "alert_type": "StockoutRisk", "severity": "Low", "description": "b"},
             {"dedup_key": "queue:race:1", "alert_type": "QueueSurge", "severity": "Medium", "description": "c"}]

    def get(self, path, query):
        return AiResult(True, {"items": self.ITEMS})


def test_ai_alerts_synced_concurrently_on_two_instances_are_created_once(db, suspicious, two_instances):
    def sync(i):
        with two_instances(i) as s:
            s.scalar(select(func.count()).select_from(AIAlert))
            return ai_alert_service.sync_from_ai(s, FakeAi(), suspicious["official"], force=True)

    results = run_parallel(sync, REFRESHES)

    assert [r for r in results if isinstance(r, Exception)] == []
    assert sum(r["created"] for r in results) == 3
    db.rollback()
    keys = db.execute(select(AIAlert.DedupKey, func.count()).where(AIAlert.Status == int(AIAlertStatus.Open))
                      .group_by(AIAlert.DedupKey)).tuples().all()
    assert sorted(keys) == [("queue:race:1", 1), ("stock:race:1", 1), ("stock:race:2", 1)]


# ---------------------------------------------------------------- lock lifecycle

def _lock_is_free(name: str) -> bool:
    with new_session() as s:
        return s.scalar(text("SELECT IS_FREE_LOCK(:n)"), {"n": name}) == 1


def test_a_refresh_that_cannot_get_the_lock_in_time_skips_and_a_later_one_succeeds(db, suspicious, monkeypatch, engine):
    from app.database import locks

    monkeypatch.setattr(locks, "WAIT_SECONDS", 1)
    with engine.connect() as holder:   # another instance in the middle of a refresh
        assert holder.scalar(text("SELECT GET_LOCK(:n, 0)"), {"n": locks.RULE_ALERTS}) == 1
        assert holder.scalar(text("SELECT GET_LOCK(:n, 0)"), {"n": locks.AI_ALERT_SYNC}) == 1
        assert _scan(new_session) == []                                       # gave up after the wait; created nothing
        with new_session() as s:
            busy = ai_alert_service.sync_from_ai(s, FakeAi(), suspicious["official"], force=True)
        assert busy["skipped"] is True and busy["created"] == 0 and busy["errorCode"] is None
        assert _alerts(db) == []
        holder.execute(text("SELECT RELEASE_ALL_LOCKS()"))
    assert len(_scan(new_session)) == 3


def test_a_refresh_that_fails_releases_the_lock_and_the_retry_succeeds(db, suspicious, monkeypatch):
    from app.database import locks

    real = ai_rules_service._upsert_alert

    def broken(*args, **kwargs):
        raise RuntimeError("simulated failure inside the refresh")

    monkeypatch.setattr(ai_rules_service, "_upsert_alert", broken)
    with pytest.raises(RuntimeError):
        _scan(new_session)
    assert _lock_is_free(locks.RULE_ALERTS) and _alerts(db) == []

    monkeypatch.setattr(ai_rules_service, "_upsert_alert", real)
    assert len(_scan(new_session)) == 3 and _lock_is_free(locks.RULE_ALERTS)


def test_a_holder_whose_connection_dies_does_not_block_anyone(db, suspicious, engine, monkeypatch):
    """A crashed instance: its connection is gone, so MySQL frees the lock; nothing waits for it to time out."""
    from app.database import locks

    monkeypatch.setattr(locks, "WAIT_SECONDS", 1)
    holder = engine.raw_connection()
    cursor = holder.cursor()
    cursor.execute("SELECT GET_LOCK(%s, 0)", (locks.RULE_ALERTS,))
    assert cursor.fetchone()[0] == 1
    with engine.connect() as admin:
        admin.execute(text(f"KILL {int(admin.scalar(text('SELECT IS_USED_LOCK(:n)'), {'n': locks.RULE_ALERTS}))}"))
    holder.invalidate()
    assert len(_scan(new_session)) == 3


def test_losing_the_lock_connection_during_a_refresh_is_survived(db, suspicious, engine, monkeypatch, caplog):
    """The lock's own connection drops mid-refresh: the refresh still finishes (its writes use the request's session),
    the failed release is logged and that connection discarded, and the next refresh can take the lock."""
    from app.database import locks

    real = ai_rules_service._upsert_alert
    killed: list[int] = []

    def kill_lock_connection_once(*args, **kwargs):
        if not killed:
            with engine.connect() as admin:
                holder = admin.scalar(text("SELECT IS_USED_LOCK(:n)"), {"n": locks.RULE_ALERTS})
                killed.append(holder)
                admin.execute(text(f"KILL {int(holder)}"))
        return real(*args, **kwargs)

    monkeypatch.setattr(ai_rules_service, "_upsert_alert", kill_lock_connection_once)
    with caplog.at_level(logging.WARNING, logger="app.database.locks"):
        assert len(_scan(new_session)) == 3
    assert killed and "not released cleanly" in caplog.text
    assert _lock_is_free(locks.RULE_ALERTS)
    monkeypatch.setattr(ai_rules_service, "_upsert_alert", real)
    assert _scan(new_session) == [] and len(_alerts(db)) == 3


# ---------------------------------------------------------------- the page itself

def test_intelligence_centre_keeps_its_access_rules_and_severities(api, db, suspicious):
    from app.security.tokens import TokenUser, create_access_token

    settings = api.app.state.settings

    def bearer(user_id: int, role: str, shop_id: int | None) -> dict:
        user = db.get(User, user_id)
        return {"Authorization": "Bearer " + create_access_token(TokenUser(user.Id, user.Email, user.FullName, role, shop_id), settings)[0]}

    official = bearer(suspicious["official"].user_id, "GovernmentOfficial", None)
    shop = bearer(suspicious["owner_id"], "ShopOwner", suspicious["shop_id"])
    assert api.get("/api/ai/intelligence-center", headers=shop).status_code == 403
    first = api.get("/api/ai/intelligence-center", headers=official)
    second = api.get("/api/ai/intelligence-center", headers=official)
    assert first.status_code == second.status_code == 200
    seen = sorted((a["alertType"], a["severity"]) for a in second.json()["data"]["recentAnomalies"])
    assert seen == [("DuplicateCollectionAttempt", "High"), ("RepeatedQrScan", "Medium"), ("RepeatedQrScan", "Medium")]
    assert second.json()["data"]["anomaliesRequiringReview"] == 3
