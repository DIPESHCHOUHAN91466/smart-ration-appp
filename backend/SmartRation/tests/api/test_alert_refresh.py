"""Rule-alert refresh: one alert per subject, one notification, and the refresh lock (2026-10-17, Phase 5).

The cross-process behaviour of the lock is tested on real MySQL (tests/integration/mysql_suite/test_11_alert_concurrency.py);
these tests cover the rules themselves and the in-process fallback used with SQLite.
"""

from __future__ import annotations

import threading
from datetime import timedelta

import pytest
from ration_world import session
from sqlalchemy import func, select

from app.database import locks
from app.database.enums import AIAlertSeverity, VerificationAction
from app.database.models import AIAlert, Notification, VerificationAuditLog
from app.services import ai_rules_service
from app.utils.time import utc_now

SHOP, OWNER = 1, 50   # the synthetic world's first shop and its owner


def _rejected(db, token: str, beneficiary_id: int, times: int = 2) -> None:
    for _ in range(times):
        db.add(VerificationAuditLog(Action=int(VerificationAction.CollectionRejected), BeneficiaryId=beneficiary_id, ShopId=SHOP,
                                    TokenNumber=token, VerificationMethod="QR", Status="BLOCKED",
                                    Timestamp=utc_now() - timedelta(minutes=5)))


def _alerts_and_notices(db) -> tuple[list[tuple], int]:
    alerts = db.execute(select(AIAlert.AlertType, AIAlert.ShopId, AIAlert.BeneficiaryId, AIAlert.Severity)).tuples().all()
    notices = db.scalar(select(func.count()).select_from(Notification).where(Notification.UserId == OWNER))
    return sorted(alerts), notices


def test_one_scan_raises_one_alert_per_subject_even_across_several_tokens(env):
    """Two tokens of the same beneficiary at the same shop, each rejected twice: the alert's subject (type, shop,
    beneficiary) is the same, so one alert and one notice, exactly as a second scan would decide."""
    with session() as db:
        _rejected(db, "TKN-A", 7)
        _rejected(db, "TKN-B", 7)
        db.commit()
        created = ai_rules_service.scan_and_detect(db)
        assert len(created) == 1
        assert _alerts_and_notices(db) == ([("DuplicateCollectionAttempt", SHOP, 7, int(AIAlertSeverity.High))], 1)
        assert ai_rules_service.scan_and_detect(db) == []   # and a later scan adds nothing


def test_different_subjects_in_one_scan_each_get_their_alert(env):
    with session() as db:
        _rejected(db, "TKN-A", 7)
        _rejected(db, "TKN-C", 8)
        db.commit()
        assert len(ai_rules_service.scan_and_detect(db)) == 2
        alerts, notices = _alerts_and_notices(db)
        assert [a[2] for a in alerts] == [7, 8] and notices == 2


def _hold(name: str, ready: threading.Event, done: threading.Event) -> None:
    with session() as db, locks.named_lock(db, name) as held:
        assert held
        ready.set()
        done.wait(10)


def test_a_scan_skips_while_another_holds_the_lock_and_runs_once_it_is_free(env, monkeypatch):
    monkeypatch.setattr(locks, "WAIT_SECONDS", 0)
    with session() as db:
        _rejected(db, "TKN-A", 7)
        db.commit()
    ready, done = threading.Event(), threading.Event()
    holder = threading.Thread(target=_hold, args=(locks.RULE_ALERTS, ready, done))
    holder.start()
    try:
        assert ready.wait(10)
        with session() as db:
            assert ai_rules_service.scan_and_detect(db) == []          # busy: skipped, nothing written
            assert _alerts_and_notices(db) == ([], 0)
    finally:
        done.set()
        holder.join(10)
    with session() as db:
        assert len(ai_rules_service.scan_and_detect(db)) == 1


def test_the_lock_is_released_when_the_scan_fails(env, monkeypatch):
    with session() as db:
        _rejected(db, "TKN-A", 7)
        db.commit()

    def broken(*args, **kwargs):
        raise RuntimeError("simulated failure inside the refresh")

    real = ai_rules_service._upsert_alert
    monkeypatch.setattr(ai_rules_service, "_upsert_alert", broken)
    with session() as db, pytest.raises(RuntimeError):
        ai_rules_service.scan_and_detect(db)
    monkeypatch.setattr(ai_rules_service, "_upsert_alert", real)
    monkeypatch.setattr(locks, "WAIT_SECONDS", 0)                     # would skip at once if the lock were still held
    with session() as db:
        assert len(ai_rules_service.scan_and_detect(db)) == 1
