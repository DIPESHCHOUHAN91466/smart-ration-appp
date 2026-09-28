"""Demand forecast for one shop and item: preprocessing -> model selection -> prediction -> uncertainty.

Confidence is derived from history length and the measured backtest error — never asserted. Below
`min_history_days` no forecast is produced at all (the caller shows "not enough data" instead).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ai.evaluation.backtest import stdev
from ai.models.forecasting import MODEL_VERSION, total_fn
from ai.preprocessing.series import cap_outliers
from ai.training.model_selection import confidence, select_method


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
    model_version: str = MODEL_VERSION


def forecast(history: list[float], horizon_days: int, min_history_days: int) -> ForecastResult:
    n = len(history)
    if n < min_history_days or sum(history) <= 0:
        return ForecastResult(history_days=n, horizon_days=horizon_days, sufficient=False)

    history, outliers = cap_outliers(history)
    chosen = select_method(history, horizon_days)

    level = confidence(n, chosen.wmape)
    if outliers and level == "HIGH":
        level = "MEDIUM"  # history needed repair: don't claim high confidence

    total = total_fn(chosen.method)(history, horizon_days)
    rate = total / horizon_days

    # ~80% band from the backtest errors.
    basis = chosen.spread_basis
    spread = stdev(basis) * 1.28 * chosen.spread_scale if len(basis) > 1 else total
    return ForecastResult(
        history_days=n,
        horizon_days=horizon_days,
        sufficient=True,
        method=chosen.method,
        daily_rate=round(rate, 2),
        forecast_total=round(total, 1),
        range_low=round(max(0.0, total - spread), 1),
        range_high=round(total + spread, 1),
        backtest_wmape=None if math.isinf(chosen.wmape) else round(chosen.wmape, 3),
        confidence=level,
        data_quality="ANOMALOUS" if outliers else "SUFFICIENT",
        outlier_days=outliers,
    )
