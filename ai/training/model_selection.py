"""Training for this system = choosing, per shop and item, the forecasting model that backtests best on
that shop's own history, and measuring how much to trust it.

There are no trained weights to store: the candidates are fixed, explainable formulas
(ai.models.forecasting), and "fitting" is selecting the one with the lowest backtest error. This runs at
request time on the latest history, so the choice follows the data as it changes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ai.evaluation.backtest import MIN_ORIGINS, horizon_backtest, horizon_origins, one_step_backtest
from ai.models.forecasting import CYCLE_DAYS, SEASONAL, SES, STEP_PREDICTORS, WMA, WMA_WINDOW


@dataclass(frozen=True)
class Selection:
    method: str
    wmape: float                  # backtest error of the chosen method (math.inf if there was no demand)
    spread_basis: list[float]     # backtest errors the uncertainty band is built from
    spread_scale: float           # 1 for horizon errors; sqrt(horizon) when built from daily errors


def candidates(n: int) -> list[str]:
    """The seasonal model is only a candidate with at least two full cycles of history."""
    return [WMA, SES, SEASONAL] if n >= 2 * CYCLE_DAYS else [WMA, SES]


def select_method(history: list[float], horizon_days: int) -> Selection:
    n = len(history)
    names = candidates(n)
    first_origin = CYCLE_DAYS if SEASONAL in names else max(WMA_WINDOW, n // 3)

    if len(horizon_origins(n, horizon_days, first_origin)) >= MIN_ORIGINS:
        # Preferred: judge each method on horizon totals (the reported number).
        scored = {name: horizon_backtest(history, name, horizon_days, first_origin) for name in names}
        method = min(scored, key=lambda name: scored[name][0])
        wmape, errors = scored[method]
        return Selection(method, wmape, errors, 1.0)

    # Short history: fall back to one-step-ahead daily errors.
    warmup = min(WMA_WINDOW, n // 2)
    scored = {name: one_step_backtest(history, STEP_PREDICTORS[name], warmup) for name in names}
    method = min(scored, key=lambda name: scored[name][0])
    wmape, residuals = scored[method]
    return Selection(method, wmape, residuals, math.sqrt(horizon_days))


def confidence(history_days: int, wmape: float) -> str:
    """LOW / MEDIUM / HIGH from how much history there is and how well the method backtested."""
    if history_days >= 60 and wmape < 0.2:
        return "HIGH"
    if history_days >= 28 and wmape < 0.4:
        return "MEDIUM"
    return "LOW"
