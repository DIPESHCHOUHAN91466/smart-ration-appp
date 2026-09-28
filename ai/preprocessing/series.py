"""Turn distribution events into the clean daily series the forecasting models read."""

from __future__ import annotations

from datetime import date, timedelta


def daily_series(events: list[tuple[date, float]], start: date, end: date) -> list[float]:
    """Dense per-day totals from start..end inclusive (days with no distribution = 0)."""
    totals: dict[date, float] = {}
    for day, qty in events:
        if start <= day <= end:
            totals[day] = totals.get(day, 0.0) + qty
    return [totals.get(start + timedelta(days=i), 0.0) for i in range((end - start).days + 1)]


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
