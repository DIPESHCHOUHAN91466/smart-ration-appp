"""Unit tests for the pure analytics modules."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from smartration_ai import forecasting, inventory, queue, risk, shop_monitor
from smartration_ai.domain import MovementType, TokenStatus, VerificationAction

# ---------------------------------------------------------------- forecasting


def test_forecast_refuses_with_insufficient_history():
    result = forecasting.forecast([10.0] * 6, horizon_days=7, min_history_days=14)
    assert not result.sufficient
    assert result.forecast_total is None and result.confidence is None


def test_forecast_refuses_all_zero_history():
    assert not forecasting.forecast([0.0] * 60, 7, 14).sufficient


def test_forecast_stable_series_is_accurate_and_confident():
    result = forecasting.forecast([20.0] * 90, horizon_days=7, min_history_days=14)
    assert result.sufficient
    assert result.daily_rate == 20.0
    assert result.forecast_total == 140.0
    assert result.confidence == "HIGH"
    assert result.range_low <= 140.0 <= result.range_high


def test_forecast_short_noisy_history_is_low_confidence():
    noisy = [0, 40, 3, 0, 35, 1, 0, 50, 2, 0, 30, 0, 5, 45, 0, 0]
    result = forecasting.forecast([float(v) for v in noisy], 30, 14)
    assert result.sufficient
    assert result.confidence == "LOW"
    assert result.forecast_total >= 0


def test_daily_series_fills_missing_days_with_zero():
    start = date(2026, 9, 1)
    series = forecasting.daily_series([(start, 5), (start + timedelta(days=2), 3), (start + timedelta(days=2), 2)], start, start + timedelta(days=3))
    assert series == [5, 0, 5, 0]


# ---------------------------------------------------------------- inventory

T = inventory.Thresholds(low_stock_days=7, critical_stock_days=3)


def _inv(stock, reorder=10, used=0.0, reserved=0.0, window=30):
    inv = [{"shop_id": 1, "ration_type": 1, "available": stock, "reorder_level": reorder}]
    dist = [{"shop_id": 1, "ration_type": 1, "quantity": used}] if used else []
    res = [{"shop_id": 1, "ration_type": 1, "quantity": reserved}] if reserved else []
    return inventory.analyse(inv, dist, [], res, window, T, "en")[0]


def test_inventory_statuses():
    assert _inv(0)["status"] == "OUT_OF_STOCK"
    assert _inv(20, used=300)["status"] == "CRITICAL"          # 10/day -> 2 days
    assert _inv(8, used=30)["status"] == "REORDER_NOW"         # below reorder level
    assert _inv(50, used=300)["status"] == "REORDER_SOON"      # 5 days
    assert _inv(500, used=300)["status"] == "OK"               # 50 days
    assert _inv(500)["status"] == "NO_USAGE_DATA"


def test_inventory_days_remaining_and_reservations():
    row = _inv(100, used=60, reserved=120)
    assert row["avg_daily_consumption"] == 2.0
    assert row["days_remaining"] == 50.0
    assert row["available_after_reservations"] == -20.0
    assert row["status"] == "REORDER_NOW"
    assert row["reasons"][0]["code"] == "STOCK_RESERVED_EXCEEDS"


def test_inventory_reasons_are_localized():
    row = inventory.analyse([{"shop_id": 1, "ration_type": 1, "available": 0, "reorder_level": 5}], [], [], [], 30, T, "hi")[0]
    assert row["reasons"][0]["text"] == "स्टॉक समाप्त।"


# ---------------------------------------------------------------- queue

BASE = datetime(2026, 9, 24, 10, 0)


def test_service_time_ignores_idle_gaps_and_days():
    times = [BASE, BASE + timedelta(minutes=3), BASE + timedelta(minutes=7), BASE + timedelta(minutes=60), BASE + timedelta(days=1)]
    assert queue.measured_service_minutes(times) == [3.0, 4.0]


def _tok(start: time, status: int, day: date = BASE.date()):
    return {"slot_date": day, "start": start, "end": (datetime.combine(day, start) + timedelta(minutes=5)).time(), "status": status}


def test_queue_uses_measured_time_when_enough_samples():
    times = [BASE + timedelta(minutes=5 * i) for i in range(7)]  # 6 gaps of 5 min
    tokens = [_tok(time(9, 0), TokenStatus.CONFIRMED), _tok(time(10, 0), TokenStatus.CONFIRMED),
              _tok(time(12, 0), TokenStatus.CONFIRMED), _tok(time(9, 30), TokenStatus.COMPLETED)]
    out = queue.analyse_shop({"Id": 1, "ShopName": "S"}, tokens, tokens, times, datetime(2026, 9, 24, 10, 2), 4.0, 5, "en")
    assert out["service_time_source"] == "MEASURED"
    assert out["avg_service_minutes"] == 5.0
    assert out["current_queue"] == 2          # 09:00 and 10:00 are due
    assert out["delayed_tokens"] == 1         # 09:00-09:05 has passed
    assert out["estimated_wait_minutes"] == 10
    assert out["served_today"] == 1


def test_queue_falls_back_to_default_and_says_so():
    out = queue.analyse_shop({"Id": 1, "ShopName": "S"}, [], [], [BASE], BASE, 4.0, 5, "en")
    assert out["service_time_source"] == "DEFAULT"
    assert out["notes"][0]["code"] == "QUEUE_DEFAULT"


# ---------------------------------------------------------------- risk

NOW = datetime(2026, 9, 24, 6, 0)
BEN = {"id": 7, "code": "BEN-0007", "user_id": 70, "assigned_shop_id": 1, "monthly_entitlement": {1: 10.0}}


def _ev(action, status="BLOCKED"):
    return {"beneficiary_id": 7, "shop_id": 1, "action": action, "status": status, "at": NOW}


def test_clean_beneficiary_is_not_flagged():
    assert risk.score_beneficiaries([BEN], [], [], [], NOW, "en") == []


def test_token_reuse_is_not_double_counted_as_blocked_verification():
    events = [_ev(VerificationAction.TOKEN_ALREADY_USED), _ev(VerificationAction.BENEFICIARY_VERIFIED)]
    result = risk.score_beneficiaries([BEN], events, [], [], NOW, "en")[0]
    assert [r["code"] for r in result["reasons"]] == ["RISK_TOKEN_REUSE"]
    assert result["risk_score"] == 15


def test_rapid_claims_other_shop_and_over_entitlement():
    collections = [
        {"beneficiary_id": 7, "shop_id": 1, "at": NOW - timedelta(hours=30), "ration_type": 1, "quantity": 5.0},
        {"beneficiary_id": 7, "shop_id": 2, "at": NOW - timedelta(hours=20), "ration_type": 1, "quantity": 5.0},
        {"beneficiary_id": 7, "shop_id": 2, "at": NOW - timedelta(hours=2), "ration_type": 1, "quantity": 5.0},
    ]
    result = risk.score_beneficiaries([BEN], [], collections, [], NOW, "en")[0]
    codes = {r["code"]: r["points"] for r in result["reasons"]}
    assert codes["RISK_RAPID_CLAIMS"] == 30        # 2 x 20, capped at 30
    assert codes["RISK_OTHER_SHOP"] == 20
    assert codes["RISK_OVER_ENTITLEMENT"] == 25    # 15 kg > 10 kg
    assert result["risk_score"] == 75 and result["risk_level"] == "HIGH"


def test_cancellation_allowance_and_score_cap():
    tokens = [{"user_id": 70, "status": TokenStatus.CANCELLED}] * 2
    assert risk.score_beneficiaries([BEN], [], [], tokens, NOW, "en") == []
    many = [_ev(VerificationAction.TOKEN_ALREADY_USED)] * 5 + [_ev(VerificationAction.COLLECTION_REJECTED)] * 5 + \
           [_ev(VerificationAction.BENEFICIARY_VERIFIED)] * 10
    tokens = [{"user_id": 70, "status": TokenStatus.CANCELLED}] * 9
    collections = [{"beneficiary_id": 7, "shop_id": 2, "at": NOW - timedelta(hours=h), "ration_type": 1, "quantity": 9.0} for h in (1, 2, 3)]
    result = risk.score_beneficiaries([BEN], many, collections, tokens, NOW, "en")[0]
    assert result["risk_score"] == 100 and result["risk_level"] == "CRITICAL"


# ---------------------------------------------------------------- shop monitoring


def _mv(i, mtype, qty, balance):
    return {"id": i, "shop_id": 1, "ration_type": 1, "type": mtype, "quantity": qty, "balance_after": balance, "at": NOW}


def test_reconcile_clean_ledger_has_no_findings():
    moves = [_mv(1, MovementType.RECEIVED, 100, 100), _mv(2, MovementType.DISTRIBUTED, 5, 95), _mv(3, MovementType.DAMAGED, 5, 90)]
    inv = [{"shop_id": 1, "ration_type": 1, "available": 90.0}]
    assert shop_monitor.reconcile(moves, inv, "en") == []


def test_reconcile_detects_off_ledger_change_and_balance_mismatch():
    moves = [_mv(1, MovementType.RECEIVED, 100, 100), _mv(2, MovementType.DISTRIBUTED, 5, 80)]  # 15 vanished
    inv = [{"shop_id": 1, "ration_type": 1, "available": 70.0}]  # 10 more vanished since
    codes = [f["code"] for f in shop_monitor.reconcile(moves, inv, "en")]
    assert codes == ["SHOP_LEDGER_GAP", "SHOP_LEDGER_MISMATCH"]


def test_shop_status_investigate_on_high_failed_verification():
    events = [{"shop_id": 1, "action": VerificationAction.BENEFICIARY_VERIFIED, "status": s} for s in ["BLOCKED"] * 4 + ["SUCCESS"] * 6]
    out = shop_monitor.analyse([{"Id": 1, "ShopName": "S"}], [], {}, [], events, [], [], date(2026, 9, 24), "en")[0]
    assert out["status"] == "INVESTIGATE"
    assert out["failed_verification_rate"] == 0.4


def test_stock_out_rejections_do_not_count_against_beneficiary():
    stock = {**_ev(VerificationAction.COLLECTION_REJECTED), "reason": "Insufficient shop inventory."}
    assert risk.score_beneficiaries([BEN], [stock, stock], [], [], NOW, "en") == []
    other = {**_ev(VerificationAction.COLLECTION_REJECTED), "reason": "Aadhaar verification is pending."}
    assert risk.score_beneficiaries([BEN], [other], [], [], NOW, "en")[0]["risk_score"] == 5

