"""The API is single-instance by design today (2026-10-17, Phase 3). These tests pin that assumption so it can't drift
silently; see docs/audit/PHASE3_RELEASE_READINESS.md, "Multi-instance readiness".

Known limitation, NOT fixed: the per-IP rate limiter keeps its counters in the process, so N processes allow N x the
limit. Fixed in Phase 5: the AI-alert refreshes take a MySQL named lock (app/database/locks.py), tested across two
instances in tests/integration/mysql_suite/test_11_alert_concurrency.py. Database-backed rules are not affected either:
booking capacity, stock, collections, idempotency keys and the daily OTP limits use row locks and unique keys and are
tested across two instances on MySQL (tests/integration/mysql_suite/test_10_collection_concurrency.py). Before running
more than one process or App Service instance, replace the in-process rate limiter (proposal in the readiness
document) and delete the first test below."""

from __future__ import annotations

import re

from py_testkit import REPO_ROOT, make_settings

from app.database import locks
from app.main import create_app
from app.services import ai_alert_service, ai_rules_service


def test_known_limitation_rate_limits_are_per_process(tmp_path):
    first, second = create_app(make_settings(tmp_path)), create_app(make_settings(tmp_path))   # two "instances"
    allowed = sum(app.state.rate_limiter.allow("auth", "203.0.113.7", 10) for app in (first, second) for _ in range(10))
    assert allowed == 20   # one client gets the limit once per process; a shared limiter would give 10


def test_the_alert_refreshes_are_guarded_by_a_database_lock_not_a_process_lock():
    assert not hasattr(ai_alert_service, "_sync_lock")
    for service in (ai_alert_service, ai_rules_service):
        assert service.named_lock is locks.named_lock
    assert locks.AI_ALERT_SYNC != locks.RULE_ALERTS and all(len(n) <= 64 for n in (locks.AI_ALERT_SYNC, locks.RULE_ALERTS))


def test_every_start_path_runs_exactly_one_api_process():
    paths = [REPO_ROOT / "scripts" / "azure" / "startup.sh", REPO_ROOT / "backend" / "SmartRation" / "Dockerfile"]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "uvicorn" in text, path
        assert not re.search(r"--workers|gunicorn|WEB_CONCURRENCY", text), f"{path} would start several processes"
