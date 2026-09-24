"""Alert candidates derived from the analytics.

The Python service stays read-only: it only *proposes* alerts. The .NET API
persists them into AIAlerts, using `dedup_key` so that re-running detection
(e.g. refreshing the dashboard) updates the open alert instead of adding a
duplicate. An alert is a prompt for human review, never proof of fraud.

Types: LOW_STOCK, FORECAST_RISK, DEMAND_SPIKE, UNUSUAL_CONSUMPTION, INVENTORY_ANOMALY
Severity: INFO / LOW / MEDIUM / HIGH / CRITICAL
"""

from __future__ import annotations

from datetime import date, timedelta

from .domain import RATION_TYPES, unit_for
from .i18n import reason

TYPE_IDS = {name: rid for rid, name in RATION_TYPES.items()}

SPIKE_RATIO = 1.8
SPIKE_MIN_QTY = 10.0
SPIKE_BASELINE_DAYS = 56


def _candidate(alert_type, severity, shop_id, ration_type, title, description, score, action, metadata):
    item = f":{ration_type}" if ration_type else ""
    return {
        "dedup_key": f"{alert_type}:{shop_id}{item}",
        "alert_type": alert_type,
        "severity": severity,
        "shop_id": shop_id,
        "ration_type": TYPE_IDS.get(ration_type) if ration_type else None,
        "title": title,
        "description": description,
        "score": round(min(100.0, max(0.0, score)), 1),
        "recommended_action": action,
        "metadata": metadata,
    }


def low_stock(inventory_rows: list[dict], lang: str) -> list[dict]:
    levels = {"OUT_OF_STOCK": ("CRITICAL", 100), "CRITICAL": ("HIGH", 85), "REORDER_NOW": ("MEDIUM", 60)}
    out = []
    for row in inventory_rows:
        if row["status"] not in levels:
            continue
        severity, score = levels[row["status"]]
        out.append(_candidate(
            "LOW_STOCK", severity, row["shop_id"], row["ration_type"],
            f"{row['ration_type']}: {row['status'].replace('_', ' ').lower()}",
            " ".join(r["text"] for r in row["reasons"]), score,
            reason("ACTION_REORDER", lang)["text"],
            {k: row[k] for k in ("stock", "reserved", "reorder_level", "avg_daily_consumption", "days_remaining", "unit")},
        ))
    return out


def forecast_risk(shop_id: int, forecast_items: list[dict], inventory_rows: list[dict], lang: str) -> list[dict]:
    """Forecast demand over the horizon exceeds stock left after reservations."""
    available = {r["ration_type"]: r["available_after_reservations"] for r in inventory_rows if r["shop_id"] == shop_id}
    out = []
    for f in forecast_items:
        if not f["data_sufficient"] or f["ration_type"] not in available:
            continue
        need, have = f["forecast_total"], available[f["ration_type"]]
        if need <= 0 or need <= have:
            continue
        ratio = need / max(have, 0.01)
        unit = f["unit"]
        out.append(_candidate(
            "FORECAST_RISK", "HIGH" if have <= 0 or ratio >= 1.5 else "MEDIUM", shop_id, f["ration_type"],
            f"{f['ration_type']}: forecast demand exceeds stock",
            reason("ALERT_FORECAST_RISK", lang, need=f"{need:g} {unit}", days=f["horizon_days"], have=f"{have:g} {unit}",
                   confidence=f["confidence"])["text"],
            40 + min(60, (ratio - 1) * 60), reason("ACTION_REORDER", lang)["text"],
            {"forecast_total": need, "available_after_reservations": have, "horizon_days": f["horizon_days"],
             "confidence": f["confidence"], "method": f.get("method"), "data_points": f["data_points"]},
        ))
    return out


def demand_spike(shop_id: int, items: list[dict], today: date, lang: str) -> list[dict]:
    """Last 7 days vs the average week over the previous 8 weeks."""
    recent_start = today - timedelta(days=7)
    base_start = recent_start - timedelta(days=SPIKE_BASELINE_DAYS)
    out = []
    for rtype, name in RATION_TYPES.items():
        rows = [r for r in items if r["shop_id"] == shop_id and r["ration_type"] == rtype]
        recent = sum(r["quantity"] for r in rows if recent_start <= r["at"].date() < today)
        base = sum(r["quantity"] for r in rows if base_start <= r["at"].date() < recent_start)
        first = min((r["at"].date() for r in rows), default=None)
        if not first or first > base_start or base <= 0:
            continue  # not enough baseline to call anything a spike
        weekly = base / (SPIKE_BASELINE_DAYS / 7)
        ratio = recent / weekly
        if recent >= SPIKE_MIN_QTY and ratio >= SPIKE_RATIO:
            unit = unit_for(name)
            out.append(_candidate(
                "DEMAND_SPIKE", "HIGH" if ratio >= 2.5 else "MEDIUM", shop_id, name,
                f"{name}: demand spike",
                reason("ALERT_DEMAND_SPIKE", lang, recent=f"{recent:g} {unit}", ratio=round(ratio, 1), weekly=f"{weekly:.1f} {unit}")["text"],
                min(100, ratio * 30), reason("ACTION_CHECK_DEMAND", lang)["text"],
                {"last_7_days": recent, "baseline_weekly_avg": round(weekly, 2), "ratio": round(ratio, 2)},
            ))
    return out


def from_shop_findings(shop_rows: list[dict], lang: str) -> list[dict]:
    mapping = {
        "SHOP_LEDGER_GAP": ("INVENTORY_ANOMALY", "HIGH", 80, "ACTION_AUDIT_STOCK"),
        "SHOP_LEDGER_MISMATCH": ("INVENTORY_ANOMALY", "HIGH", 85, "ACTION_AUDIT_STOCK"),
        "SHOP_HIGH_DAMAGE": ("UNUSUAL_CONSUMPTION", "MEDIUM", 55, "ACTION_REVIEW_DAMAGE"),
        "SHOP_UNDER_ISSUE": ("UNUSUAL_CONSUMPTION", "LOW", 40, "ACTION_REVIEW_ISSUE"),
    }
    out = []
    for shop in shop_rows:
        for f in shop["findings"]:
            if f["code"] not in mapping:
                continue
            alert_type, severity, score, action = mapping[f["code"]]
            item = f["params"].get("item")
            out.append(_candidate(
                alert_type, severity, shop["shop_id"], item, f"{shop['shop_name']}: {f['code'].replace('SHOP_', '').replace('_', ' ').lower()}",
                f["text"], score, reason(action, lang)["text"], {"finding": f["code"], **f["params"]},
            ))
    return out
