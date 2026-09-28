"""The forecasting stages on their own — preprocessing, models, evaluation, training, inference — and the
accuracy report that monitors them."""

from __future__ import annotations

import json
import math
from datetime import date, timedelta

import pytest

from ai.evaluation import report
from ai.evaluation.backtest import horizon_backtest, one_step_backtest
from ai.inference.forecast import forecast
from ai.inference.service import AnalyticsService
from ai.models.forecasting import MODEL_VERSION, SEASONAL, SES, WMA, ses_next, total_fn, wma_next
from ai.preprocessing.series import cap_outliers, daily_series
from ai.training.model_selection import candidates, confidence, select_method

from ai_testkit import NOW


def test_daily_series_fills_missing_days_with_zero_and_ignores_out_of_range():
    start = date(2026, 9, 1)
    events = [(start, 2.0), (start, 3.0), (start + timedelta(days=2), 4.0), (start - timedelta(days=1), 99.0)]
    assert daily_series(events, start, start + timedelta(days=3)) == [5.0, 0.0, 4.0, 0.0]


def test_a_single_data_entry_spike_is_capped_and_counted():
    history = [8.0, 9.0, 10.0, 11.0, 12.0] * 3 + [500.0]
    capped, outliers = cap_outliers(history)
    assert outliers == 1 and max(capped) < 500 and capped[:15] == history[:15]


def test_models_on_known_series():
    assert wma_next([1.0, 2.0, 3.0]) == pytest.approx((1 + 4 + 9) / 6)
    assert ses_next([10.0, 10.0, 10.0]) == 10.0
    assert total_fn(WMA)([5.0] * 14, 7) == 35.0


def test_backtests_measure_error_against_what_actually_happened():
    flat = [5.0] * 40
    wmape, residuals = one_step_backtest(flat, wma_next, warmup=7)
    assert wmape == 0.0 and all(r == 0 for r in residuals)
    wmape_h, _ = horizon_backtest(flat, WMA, 7, first_origin=7)
    assert wmape_h == 0.0
    assert one_step_backtest([0.0] * 20, wma_next, 7)[0] == math.inf  # no demand: error undefined, not 0


def test_training_only_offers_the_seasonal_model_with_two_cycles_of_history():
    assert SEASONAL not in candidates(59) and SEASONAL in candidates(60)


def test_training_picks_the_seasonal_model_for_a_monthly_pattern():
    month = [30.0] * 5 + [2.0] * 25            # most families collect in the first days of the cycle
    history = month * 4
    chosen = select_method(history, horizon_days=7)
    assert chosen.method == SEASONAL and chosen.wmape < 0.2
    assert select_method([5.0] * 30, 7).method in (WMA, SES)


def test_confidence_needs_both_history_and_accuracy():
    assert confidence(90, 0.1) == "HIGH"
    assert confidence(30, 0.1) == "MEDIUM" and confidence(90, 0.5) == "LOW" and confidence(10, 0.0) == "LOW"


def test_inference_reports_model_version_and_refuses_thin_history():
    thin = forecast([5.0] * 5, 7, min_history_days=14)
    assert not thin.sufficient and thin.forecast_total is None
    good = forecast([5.0] * 30, 7, min_history_days=14)
    assert good.sufficient and good.forecast_total == 35.0 and good.model_version == MODEL_VERSION


def _history(db, days=30):
    shop = db.shop("Satnavari")
    ben = db.beneficiary(shop, user_id=10)
    for d in range(1, days + 1):
        at = NOW - timedelta(days=d)
        tok = db.token(shop, 10, at.replace(hour=4), 3, collected_at=at)
        db.collection(shop, ben, at, rice=5, token_id=tok)
    return shop


def test_accuracy_report_lists_every_shop_and_item(db, settings, repo):
    _history(db)
    rows = report.evaluate(AnalyticsService(repo, settings, clock=lambda: NOW), repo, horizon_days=7)
    rice = next(r for r in rows if r.item == "Rice")
    assert rice.sufficient_data and rice.backtest_wmape == 0.0 and rice.method
    summary = report.summarize(rows, 7)
    assert summary.model_version == MODEL_VERSION and summary.forecasts >= 1 and summary.insufficient >= 1


def test_accuracy_report_command_line_json(db, settings, repo, capsys):
    _history(db)
    assert report.main(["--json"], settings=settings) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["summary"]["model_version"] == MODEL_VERSION and any(r["item"] == "Rice" for r in out["rows"])


def test_forecast_api_exposes_the_model_version(db, settings, repo):
    from fastapi.testclient import TestClient

    from ai.api.main import create_app

    from ai_testkit import API_KEY

    _history(db)
    client = TestClient(create_app(settings=settings, repo=repo))
    items = client.get("/v1/forecast?shop_id=1&horizon_days=7", headers={"X-API-Key": API_KEY}).json()["data"]["items"]
    assert {i["model_version"] for i in items} == {MODEL_VERSION}
    assert client.get("/health").json()["forecast_model"] == MODEL_VERSION


def test_identical_days_are_never_treated_as_outliers():
    # MAD is 0 when (almost) every day is the same: no robust scale, so nothing is capped.
    assert cap_outliers([10.0] * 15 + [500.0]) == ([10.0] * 15 + [500.0], 0)
