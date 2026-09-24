"""Inventory intelligence: consumption, days of stock left, reservations, reorder status.

Input: current Inventory balances, issued items and ledger movements in the
analysis window, and items reserved by upcoming booked tokens.
Output per shop x item: received / distributed / damaged in the window,
reserved stock, average daily consumption, estimated days remaining and a
reorder status with the reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from .domain import RATION_TYPES, MovementType, unit_for
from .i18n import reason


@dataclass(frozen=True)
class Thresholds:
    low_stock_days: float
    critical_stock_days: float


# Worst first — used to sort and to summarise a shop.
STATUS_ORDER = ["OUT_OF_STOCK", "CRITICAL", "REORDER_NOW", "REORDER_SOON", "OK", "NO_USAGE_DATA"]


def analyse(
    inventory: list[dict],
    distributed: list[dict],
    movements: list[dict],
    reserved: list[dict],
    window_days: int,
    thresholds: Thresholds,
    lang: str,
) -> list[dict]:
    used: dict[tuple, float] = {}
    for row in distributed:
        key = (row["shop_id"], row["ration_type"])
        used[key] = used.get(key, 0.0) + row["quantity"]

    ledger: dict[tuple, dict[int, float]] = {}
    for m in movements:
        bucket = ledger.setdefault((m["shop_id"], m["ration_type"]), {})
        bucket[m["type"]] = bucket.get(m["type"], 0.0) + m["quantity"]

    booked: dict[tuple, float] = {}
    for r in reserved:
        key = (r["shop_id"], r["ration_type"])
        booked[key] = booked.get(key, 0.0) + r["quantity"]

    results = []
    for item in inventory:
        key = (item["shop_id"], item["ration_type"])
        name = RATION_TYPES.get(item["ration_type"], str(item["ration_type"]))
        unit = unit_for(name)
        stock = item["available"]
        reorder_level = item["reorder_level"]
        daily = used.get(key, 0.0) / window_days if window_days > 0 else 0.0
        days_left = round(stock / daily, 1) if daily > 0 else None
        reserved_qty = booked.get(key, 0.0)
        status, why = _status(stock, reorder_level, days_left, reserved_qty, thresholds, unit, lang)
        flows = ledger.get(key, {})

        results.append({
            "shop_id": item["shop_id"],
            "ration_type": name,
            "unit": unit,
            "stock": round(stock, 2),
            "reserved": round(reserved_qty, 2),
            "available_after_reservations": round(stock - reserved_qty, 2),
            "reorder_level": round(reorder_level, 2),
            "received": round(flows.get(MovementType.RECEIVED, 0.0), 2),
            "distributed": round(used.get(key, 0.0), 2),
            "damaged": round(flows.get(MovementType.DAMAGED, 0.0), 2),
            "avg_daily_consumption": round(daily, 2),
            "days_remaining": days_left,
            "status": status,
            "reasons": why,
        })

    results.sort(key=lambda r: (STATUS_ORDER.index(r["status"]), r["days_remaining"] if r["days_remaining"] is not None else 1e9))
    return results


def _status(stock, reorder_level, days_left, reserved_qty, t: Thresholds, unit, lang):
    fmt = lambda v: f"{v:g} {unit}"  # noqa: E731
    reasons = []
    if stock <= 0:
        return "OUT_OF_STOCK", [reason("STOCK_OUT", lang)]
    if reserved_qty > stock:
        reasons.append(reason("STOCK_RESERVED_EXCEEDS", lang, reserved=fmt(reserved_qty), stock=fmt(stock)))
    if days_left is not None and days_left <= t.critical_stock_days:
        return "CRITICAL", [reason("STOCK_CRITICAL", lang, days=days_left)] + reasons
    if stock <= reorder_level:
        return "REORDER_NOW", [reason("STOCK_BELOW_REORDER", lang, stock=fmt(stock), level=fmt(reorder_level))] + reasons
    if reasons:
        return "REORDER_NOW", reasons
    if days_left is not None and days_left <= t.low_stock_days:
        return "REORDER_SOON", [reason("STOCK_LOW_DAYS", lang, days=days_left)]
    if days_left is None:
        return "NO_USAGE_DATA", [reason("STOCK_NO_USAGE", lang)]
    return "OK", []

