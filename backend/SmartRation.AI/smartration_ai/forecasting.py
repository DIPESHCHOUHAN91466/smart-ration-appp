"""Demand forecasting from daily distribution history.

Deliberately simple, explainable methods (the dataset is small):
  * weighted moving average (WMA) over the last 7 days, linear weights
  * simple exponential smoothing (SES), alpha = 0.3
The method with the lower one-step-ahead backtest error on the history is
used. Confidence is derived from history length and that measured error —
never asserted. Below `min_history_days` no forecast is produced at all.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

WMA_WINDOW = 7
SES_ALPHA = 0.3
# Ration uptake follows the monthly distribution cycle: most families collect
# early in the month. The seasonal method averages the same point in the last
# few ~30-day cycles; it only wins if the backtest says it predicts better.
CYCLE_DAYS = 30
MAX_CYCLES = 3


@dataclass
class ForecastResult:
    history_days: int
    horizon_days: int
    sufficient: bool
    method: str | None = None
    daily_rate: float | None = None
    forecast_total: float | None = None
    range_low: float | None = None
    range_high: float | None = None
    backtest_wmape: float | None = None  # weighted mean absolute % error, 0..1+
    confidence: str | None = None  # LOW / MEDIUM / HIGH
    data_quality: str = "INSUFFICIENT"  # INSUFFICIENT / SUFFICIENT / ANOMALOUS
    outlier_days: int = 0


def daily_series(events: list[tuple[date, float]], start: date, end: date) -> list[float]:
    """Dense per-day totals from start..end inclusive (days with no distribution = 0)."""
    totals: dict[date, float] = {}
    for day, qty in events:
        if start <= day <= end:
            totals[day] = totals.get(day, 0.0) + qty
    return [totals.get(start + timedelta(days=i), 0.0) for i in range((end - start).days + 1)]


def wma_next(history: list[float], window: int = WMA_WINDOW) -> float:
    recent = history[-window:]
    weights = range(1, len(recent) + 1)
    return sum(w * v for w, v in zip(weights, recent)) / sum(weights)


def ses_next(history: list[float], alpha: float = SES_ALPHA) -> float:
    level = history[0]
    for value in history[1:]:
        level = alpha * value + (1 - alpha) * level
    return level


def seasonal_next(history: list[float]) -> float:
    cycles = min(MAX_CYCLES, len(history) // CYCLE_DAYS)
    if cycles == 0:
        return wma_next(history)
    n = len(history)
    return sum(history[n - CYCLE_DAYS * c] for c in range(1, cycles + 1)) / cycles


def seasonal_total(history: list[float], horizon: int) -> float:
    """Sum over the next `horizon` days of the same days in previous cycles."""
    cycles = min(MAX_CYCLES, len(history) // CYCLE_DAYS)
    n = len(history)
    total = 0.0
    for j in range(horizon):
        lags = [n + j - CYCLE_DAYS * c for c in range(1, cycles + 1) if n + j - CYCLE_DAYS * c < n]
        total += sum(history[i] for i in lags) / len(lags) if lags else 0.0
    return total


def _backtest(history: list[float], predictor, warmup: int) -> tuple[float, list[float]]:
    """One-step-ahead errors from `warmup` onward. Returns (wMAPE, residuals)."""
    residuals = []
    for i in range(warmup, len(history)):
        residuals.append(history[i] - predictor(history[:i]))
    actual_total = sum(abs(v) for v in history[warmup:])
    wmape = sum(abs(r) for r in residuals) / actual_total if actual_total > 0 else math.inf
    return wmape, residuals


def _confidence(history_days: int, wmape: float) -> str:
    if history_days >= 60 and wmape < 0.2:
        return "HIGH"
    if history_days >= 28 and wmape < 0.4:
        return "MEDIUM"
    return "LOW"


def cap_outliers(history: list[float], threshold: float = 5.0) -> tuple[list[float], int]:
    """Robust outlier check (median absolute deviation). Days more than
    `threshold` robust z-scores above the median — e.g. a data-entry spike —
    are capped at that bound so one bad day can't drive the forecast."""
    nonzero = sorted(v for v in history if v > 0)
    if len(nonzero) < 5:
        return history, 0
    median = nonzero[len(nonzero) // 2]
    mad = sorted(abs(v - median) for v in nonzero)[len(nonzero) // 2]
    if mad == 0:
        return history, 0
    bound = median + threshold * 1.4826 * mad
    capped = [min(v, bound) for v in history]
    return capped, sum(1 for v in history if v > bound)


HORIZON_BACKTEST_DAYS = 84  # evaluate horizon totals over the last ~12 weeks
MIN_ORIGINS = 3


def _total_fn(name: str):
    if name == "monthly-cycle seasonal average":
        return lambda h, horizon: max(0.0, seasonal_total(h, horizon))
    step = wma_next if name == "weighted moving average" else ses_next
    return lambda h, horizon: max(0.0, step(h)) * horizon


def _horizon_backtest(history: list[float], name: str, horizon: int, first_origin: int) -> tuple[float, list[float]]:
    """Rolling-origin backtest of what is actually reported: the total over
    the next `horizon` days. Origins every 7 days over the recent past."""
    total = _total_fn(name)
    n = len(history)
    errors, actual_sum = [], 0.0
    for origin in range(max(first_origin, n - horizon - HORIZON_BACKTEST_DAYS), n - horizon + 1, 7):
        actual = sum(history[origin:origin + horizon])
        errors.append(total(history[:origin], horizon) - actual)
        actual_sum += actual
    wmape = sum(abs(e) for e in errors) / actual_sum if actual_sum > 0 else math.inf
    return wmape, errors


def forecast(history: list[float], horizon_days: int, min_history_days: int) -> ForecastResult:
    n = len(history)
    if n < min_history_days or sum(history) <= 0:
        return ForecastResult(history_days=n, horizon_days=horizon_days, sufficient=False)

    history, outliers = cap_outliers(history)

    names = ["weighted moving average", "exponential smoothing"]
    if n >= 2 * CYCLE_DAYS:
        names.append("monthly-cycle seasonal average")
    first_origin = CYCLE_DAYS if len(names) == 3 else max(WMA_WINDOW, n // 3)

    origins = len(range(max(first_origin, n - horizon_days - HORIZON_BACKTEST_DAYS), n - horizon_days + 1, 7))
    if origins >= MIN_ORIGINS:
        # Preferred: judge each method on horizon totals (the reported number).
        scored = {name: _horizon_backtest(history, name, horizon_days, first_origin) for name in names}
        method = min(scored, key=lambda name: scored[name][0])
        wmape, errors = scored[method]
        spread_basis = errors
        spread_scale = 1.0
    else:
        # Short history: fall back to one-step-ahead daily errors.
        steps = {"weighted moving average": wma_next, "exponential smoothing": ses_next, "monthly-cycle seasonal average": seasonal_next}
        warmup = min(WMA_WINDOW, n // 2)
        scored = {name: _backtest(history, steps[name], warmup) for name in names}
        method = min(scored, key=lambda name: scored[name][0])
        wmape, spread_basis = scored[method]
        spread_scale = math.sqrt(horizon_days)

    confidence = _confidence(n, wmape)
    if outliers and confidence == "HIGH":
        confidence = "MEDIUM"  # history needed repair: don't claim high confidence

    total = _total_fn(method)(history, horizon_days)
    rate = total / horizon_days

    # ~80% band from the backtest errors.
    spread = _stdev(spread_basis) * 1.28 * spread_scale if len(spread_basis) > 1 else total
    return ForecastResult(
        history_days=n,
        horizon_days=horizon_days,
        sufficient=True,
        method=method,
        daily_rate=round(rate, 2),
        forecast_total=round(total, 1),
        range_low=round(max(0.0, total - spread), 1),
        range_high=round(total + spread, 1),
        backtest_wmape=None if math.isinf(wmape) else round(wmape, 3),
        confidence=confidence,
        data_quality="ANOMALOUS" if outliers else "SUFFICIENT",
        outlier_days=outliers,
    )


def _stdev(values: list[float]) -> float:
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
