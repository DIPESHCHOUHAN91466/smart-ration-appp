"""Integration tests: HTTP -> service -> repository -> SQLite."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from smartration_ai.domain import TokenStatus, VerificationAction
from smartration_ai.main import create_app
from smartration_ai.repository import Repository
from smartration_ai.service import AnalyticsService

from ai_testkit import API_KEY, NOW

H = {"X-Api-Key": API_KEY}


def client(settings, repo) -> TestClient:
    service = AnalyticsService(repo, settings, clock=lambda: NOW)
    return TestClient(create_app(settings, repo, service), raise_server_exceptions=False)


def seed(db):
    shop = db.shop("Satnavari")
    other = db.shop("Koradi")
    ben = db.beneficiary(shop, user_id=10)
    db.insert("Inventory", RationShopId=shop, RationType=1, AvailableQuantity="40", AllocatedQuantity="0", MinimumStockLevel="10", UpdatedAt="2026-09-01 00:00:00")
    # 20 days of steady history: 5 kg of rice a day.
    for d in range(1, 21):
        at = NOW - timedelta(days=d)
        tok = db.token(shop, 10, at.replace(hour=4), TokenStatus.COMPLETED, collected_at=at)
        db.collection(shop, ben, at, rice=5, token_id=tok)
    db.audit(ben, shop, VerificationAction.TOKEN_ALREADY_USED, "BLOCKED", NOW - timedelta(hours=1))
    return shop, other, ben


def test_health_reports_database(settings, repo):
    body = client(settings, repo).get("/health").json()
    assert body["status"] == "HEALTHY" and body["database"] == "CONNECTED"


def test_endpoints_require_api_key(settings, repo):
    c = client(settings, repo)
    for path in ["/v1/forecast", "/v1/inventory", "/v1/queue", "/v1/risk/beneficiaries", "/v1/shops/monitor"]:
        r = c.get(path, headers={"X-Api-Key": "wrong"})
        assert r.status_code == 401
        assert r.json() == {"success": False, "error_code": "UNAUTHORIZED", "message": "Missing or invalid API key."}


def test_invalid_input_returns_structured_422(settings, repo):
    r = client(settings, repo).get("/v1/forecast?lang=fr&horizon_days=0", headers=H)
    assert r.status_code == 422
    assert r.json()["error_code"] == "INVALID_INPUT"


def test_forecast_from_database_history(db, settings, repo):
    shop, _, _ = seed(db)
    data = client(settings, repo).get(f"/v1/forecast?shop_id={shop}&horizon_days=7", headers=H).json()["data"]
    rice = next(i for i in data["items"] if i["ration_type"] == "Rice")
    assert rice["sufficient_data"] and rice["history_days"] == 20
    assert rice["forecast_total"] == 35.0
    wheat = next(i for i in data["items"] if i["ration_type"] == "Wheat")
    assert not wheat["sufficient_data"]


def test_inventory_queue_risk_and_shops_from_database(db, settings, repo):
    shop, _, ben = seed(db)
    c = client(settings, repo)

    inv = c.get(f"/v1/inventory?shop_id={shop}", headers=H).json()["data"]["items"][0]
    assert inv["distributed"] == 100.0           # 20 days x 5 kg in the 30-day window
    assert inv["days_remaining"] == 12.0         # 40 kg / (100/30 per day)

    q = c.get(f"/v1/queue?shop_id={shop}", headers=H).json()["data"]["shops"][0]
    assert q["service_time_source"] == "DEFAULT"  # one collection a day -> no busy-period samples

    r = c.get("/v1/risk/beneficiaries?lang=mr", headers=H).json()["data"]
    assert r["items"][0]["beneficiary_id"] == ben
    # 5 kg/day against a 10 kg/month entitlement, plus one token-reuse attempt.
    assert {x["code"] for x in r["items"][0]["reasons"]} == {"RISK_OVER_ENTITLEMENT", "RISK_TOKEN_REUSE"}
    assert r["disclaimer"]["text"].startswith("फक्त निर्णय सहाय्य")

    s = c.get("/v1/shops/monitor", headers=H).json()["data"]["shops"]
    assert {x["shop_id"] for x in s} == {1, 2}


def test_shop_filter_excludes_other_shops(db, settings, repo):
    _, other, _ = seed(db)
    data = client(settings, repo).get(f"/v1/inventory?shop_id={other}", headers=H).json()["data"]
    assert data["items"] == []


def test_database_down_returns_503_without_details(settings, tmp_path):
    broken = replace(settings, db_url=f"sqlite:///{(tmp_path / 'missing' / 'nope.db').as_posix()}")
    repo = Repository(create_engine(broken.db_url))
    c = client(broken, repo)
    assert c.get("/health").json()["status"] == "DEGRADED"
    r = c.get("/v1/forecast", headers=H)
    assert r.status_code == 503
    assert r.json() == {"success": False, "error_code": "DATABASE_UNAVAILABLE", "message": "The database is temporarily unavailable. Please retry."}


def test_unexpected_error_does_not_leak_stack_trace(settings, repo):
    class Boom(AnalyticsService):
        def forecast(self, *a, **k):
            raise RuntimeError("secret internal detail")

    c = TestClient(create_app(settings, repo, Boom(repo, settings)), raise_server_exceptions=False)
    r = c.get("/v1/forecast", headers=H)
    assert r.status_code == 500
    assert "secret" not in r.text and r.json()["error_code"] == "AI_INTERNAL_ERROR"
