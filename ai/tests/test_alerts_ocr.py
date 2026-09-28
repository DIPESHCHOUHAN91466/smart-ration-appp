"""Forecast data quality, alert candidates and optional OCR."""

from __future__ import annotations

import base64
from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from ai.api.main import create_app
from ai.inference import forecast as forecasting
from ai.inference import ocr
from ai.inference.service import AnalyticsService
from ai.pipelines import alerts

from ai_testkit import API_KEY, NOW

H = {"X-Api-Key": API_KEY}
PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64).decode()

# ---------------------------------------------------------------- forecast data quality


def test_sufficient_history_is_marked_sufficient():
    r = forecasting.forecast([10.0, 12.0, 11.0, 9.0] * 10, 7, 14)
    assert r.sufficient and r.data_quality == "SUFFICIENT" and r.outlier_days == 0


def test_outlier_day_is_capped_and_flagged_anomalous():
    history = [10.0, 11.0, 9.0, 10.0, 12.0] * 12
    history[30] = 900.0  # data-entry spike
    r = forecasting.forecast(history, 7, 14)
    assert r.data_quality == "ANOMALOUS" and r.outlier_days == 1
    assert r.forecast_total < 150  # the spike did not drive the forecast
    assert r.confidence != "HIGH"


def test_api_forecast_contract_fields(db, settings, repo):
    shop = db.shop()
    ben = db.beneficiary(shop, 10)
    for d in range(1, 31):
        db.collection(shop, ben, NOW - timedelta(days=d), rice=4)
    c = TestClient(create_app(settings, repo, AnalyticsService(repo, settings, clock=lambda: NOW)))
    items = c.get(f"/v1/forecast?shop_id={shop}", headers=H).json()["data"]["items"]
    rice = next(i for i in items if i["ration_type"] == "Rice")
    assert rice["data_sufficient"] and rice["data_points"] == 30 and rice["minimum_required"] == 14
    assert rice["forecast"] == 28.0 and rice["confidence"] and rice["limitations"]
    sugar = next(i for i in items if i["ration_type"] == "Sugar")
    assert sugar["data_sufficient"] is False and sugar["forecast"] is None
    assert sugar["limitations"][0]["code"] == "FORECAST_INSUFFICIENT_DATA"


# ---------------------------------------------------------------- alerts


def _inv_row(status, shop=1, item="Rice"):
    return {"shop_id": shop, "ration_type": item, "status": status, "reasons": [{"text": "why"}], "stock": 0.0, "reserved": 0.0,
            "reorder_level": 10.0, "avg_daily_consumption": 1.0, "days_remaining": None, "unit": "kg", "available_after_reservations": 0.0}


def test_low_stock_alerts_map_severity_and_have_stable_keys():
    out = alerts.low_stock([_inv_row("OUT_OF_STOCK"), _inv_row("CRITICAL", item="Wheat"), _inv_row("OK", item="Salt")], "en")
    assert [(a["dedup_key"], a["severity"]) for a in out] == [("LOW_STOCK:1:Rice", "CRITICAL"), ("LOW_STOCK:1:Wheat", "HIGH")]
    assert out[0]["ration_type"] == 1 and out[0]["recommended_action"]
    # Same input -> same keys: the API can deduplicate on repeated detection.
    assert [a["dedup_key"] for a in alerts.low_stock([_inv_row("OUT_OF_STOCK")], "en")] == ["LOW_STOCK:1:Rice"]


def test_demand_spike_needs_baseline_and_ratio():
    today = date(2026, 9, 24)
    rows = [{"shop_id": 1, "ration_type": 1, "quantity": 5.0, "at": datetime.combine(today - timedelta(days=d), datetime.min.time())}
            for d in range(8, 70, 7)]  # ~5 kg/week baseline
    rows += [{"shop_id": 1, "ration_type": 1, "quantity": 20.0, "at": datetime.combine(today - timedelta(days=d), datetime.min.time())} for d in (1, 3)]
    spike = alerts.demand_spike(1, rows, today, "en")
    assert len(spike) == 1 and spike[0]["alert_type"] == "DEMAND_SPIKE" and spike[0]["severity"] == "HIGH"
    # No baseline history -> no spike claimed.
    assert alerts.demand_spike(1, rows[-2:], today, "en") == []


def test_forecast_risk_only_when_forecast_exceeds_available():
    f = [{"ration_type": "Rice", "unit": "kg", "data_sufficient": True, "forecast_total": 30.0, "horizon_days": 7,
          "confidence": "MEDIUM", "method": "x", "data_points": 40}]
    inv = [{**_inv_row("OK"), "available_after_reservations": 10.0}]
    assert alerts.forecast_risk(1, f, inv, "en")[0]["severity"] == "HIGH"
    inv[0]["available_after_reservations"] = 50.0
    assert alerts.forecast_risk(1, f, inv, "en") == []
    f[0]["data_sufficient"] = False
    assert alerts.forecast_risk(1, f, [{**_inv_row("OK"), "available_after_reservations": 1.0}], "en") == []


def test_alerts_endpoint_returns_candidates(db, settings, repo):
    shop = db.shop()
    db.insert("Inventory", RationShopId=shop, RationType=1, AvailableQuantity="0", AllocatedQuantity="0", MinimumStockLevel="10", UpdatedAt="2026-09-01 00:00:00")
    c = TestClient(create_app(settings, repo, AnalyticsService(repo, settings, clock=lambda: NOW)))
    data = c.get("/v1/alerts", headers=H).json()["data"]
    assert data["count"] == 1 and data["items"][0]["dedup_key"] == f"LOW_STOCK:{shop}:Rice"


# ---------------------------------------------------------------- OCR


class FakeEngine(ocr.OcrEngine):
    name = "fake"

    def available(self):
        return True

    def extract_text(self, image):
        return "Name: Sunita Patil Aadhaar 1234 5678 9012 Mobile 9876543210 DOB 01/02/1985 Ration Card No: MH-12-3456789 Female", 0.9


def test_redaction_never_leaks_full_aadhaar_or_mobile():
    text = "Aadhaar 1234 5678 9012, alt 123456789012, phone +91 9876543210"
    red = ocr.redact(text)
    assert "5678" not in red and "56789012" not in red and "98765" not in red
    assert "XXXX-XXXX-9012" in red and "******3210" in red


def test_field_extraction_is_masked_and_never_authoritative():
    res = ocr.result(FakeEngine().extract_text(b"")[0], "fake", 0.9)
    f = res["fields"]
    assert f["aadhaar_masked"]["value"] == "XXXX-XXXX-9012"
    assert f["mobile_masked"]["value"] == "******3210"
    assert f["name"]["value"].startswith("Sunita Patil")
    assert f["ration_card_number"]["value"] == "MH-12-3456789"
    assert 0 < f["aadhaar_masked"]["confidence"] < f["gender"]["confidence"] <= 0.9
    assert res["requires_human_confirmation"] is True and res["authoritative"] is False
    assert "1234 5678" not in res["text_redacted"]


def test_ocr_unavailable_engine_returns_503(settings, repo):
    c = TestClient(create_app(settings, repo, ocr_engine=ocr.UnavailableEngine()))
    r = c.post("/v1/ocr/extract", json={"image_base64": PNG}, headers=H)
    assert r.status_code == 503 and r.json()["error_code"] == "OCR_ENGINE_UNAVAILABLE"
    assert c.get("/health").json()["ocr_engine"] == "unavailable"


def test_ocr_with_engine_and_input_validation(settings, repo):
    c = TestClient(create_app(settings, repo, ocr_engine=FakeEngine()))
    ok = c.post("/v1/ocr/extract", json={"image_base64": PNG}, headers=H).json()["data"]
    assert ok["engine"] == "fake" and ok["fields"]["aadhaar_masked"]["value"] == "XXXX-XXXX-9012"
    gif = base64.b64encode(b"GIF89a" + b"\x00" * 64).decode()
    assert c.post("/v1/ocr/extract", json={"image_base64": gif}, headers=H).json()["error_code"] == "INVALID_INPUT"
    assert c.post("/v1/ocr/extract", json={"image_base64": "not-base64!!!!!!!!"}, headers=H).status_code == 422


def test_ocr_parse_text_path(settings, repo):
    c = TestClient(create_app(settings, repo, ocr_engine=ocr.UnavailableEngine()))
    data = c.post("/v1/ocr/parse-text", json={"text": "नाम: राहुल पाटील 4321 8765 1111"}, headers=H).json()["data"]
    assert data["fields"]["aadhaar_masked"]["value"] == "XXXX-XXXX-1111"
    assert data["engine"] == "manual-text"
