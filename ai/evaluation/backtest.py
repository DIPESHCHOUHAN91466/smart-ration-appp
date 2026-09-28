"""How well a forecasting model would have predicted the past: backtests and their error measures.

wMAPE (weighted mean absolute percentage error) = sum(|error|) / sum(actual). It stays meaningful on
days with zero distribution, where plain MAPE is undefined.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from ai.models.forecasting import total_fn

HORIZON_BACKTEST_DAYS = 84  # evaluate horizon totals over the last ~12 weeks
MIN_ORIGINS = 3


def one_step_backtest(history: list[float], predictor: Callable[[list[float]], float], warmup: int) -> tuple[float, list[float]]:
    """One-step-ahead errors from `warmup` onward. Returns (wMAPE, residuals)."""
    residuals = []
    for i in range(warmup, len(history)):
        residuals.append(history[i] - predictor(history[:i]))
    actual_total = sum(abs(v) for v in history[warmup:])
    wmape = sum(abs(r) for r in residuals) / actual_total if actual_total > 0 else math.inf
    return wmape, residuals


def horizon_origins(n: int, horizon: int, first_origin: int) -> range:
    """Rolling forecast origins every 7 days over the recent past."""
    return range(max(first_origin, n - horizon - HORIZON_BACKTEST_DAYS), n - horizon + 1, 7)


def horizon_backtest(history: list[float], name: str, horizon: int, first_origin: int) -> tuple[float, list[float]]:
    """Rolling-origin backtest of what is actually reported: the total over the next `horizon` days.
    Returns (wMAPE, errors)."""
    total = total_fn(name)
    errors, actual_sum = [], 0.0
    for origin in horizon_origins(len(history), horizon, first_origin):
        actual = sum(history[origin:origin + horizon])
        errors.append(total(history[:origin], horizon) - actual)
        actual_sum += actual
    wmape = sum(abs(e) for e in errors) / actual_sum if actual_sum > 0 else math.inf
    return wmape, errors


def stdev(values: list[float]) -> float:
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
