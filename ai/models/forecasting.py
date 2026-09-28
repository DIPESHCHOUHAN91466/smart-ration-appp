"""The demand-forecasting models: deliberately simple, explainable methods (the dataset is small).

  * weighted moving average (WMA) over the last 7 days, linear weights
  * simple exponential smoothing (SES), alpha = 0.3
  * monthly-cycle seasonal average: ration uptake follows the monthly distribution cycle (most families
    collect early in the month), so this averages the same point in the last few ~30-day cycles

Each model is a pure function of the history. Which one is used for a shop and item is decided by
backtest in app code (ai.training.model_selection), never assumed.
"""

from __future__ import annotations

from collections.abc import Callable

MODEL_VERSION = "forecast-2026.09"  # bump when a model, a parameter or the selection rule changes

WMA_WINDOW = 7
SES_ALPHA = 0.3
CYCLE_DAYS = 30
MAX_CYCLES = 3

WMA = "weighted moving average"
SES = "exponential smoothing"
SEASONAL = "monthly-cycle seasonal average"


def wma_next(history: list[float], window: int = WMA_WINDOW) -> float:
    recent = history[-window:]
    weights = range(1, len(recent) + 1)
    return sum(w * v for w, v in zip(weights, recent, strict=True)) / sum(weights)


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


# One-step-ahead predictor of each model (used for short histories).
STEP_PREDICTORS: dict[str, Callable[[list[float]], float]] = {WMA: wma_next, SES: ses_next, SEASONAL: seasonal_next}


def total_fn(name: str) -> Callable[[list[float], int], float]:
    """The model's forecast of the TOTAL over the next `horizon` days — the number that is reported."""
    if name == SEASONAL:
        return lambda h, horizon: max(0.0, seasonal_total(h, horizon))
    step = wma_next if name == WMA else ses_next
    return lambda h, horizon: max(0.0, step(h)) * horizon
