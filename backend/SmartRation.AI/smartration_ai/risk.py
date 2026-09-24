"""Beneficiary risk scoring (0-100) — DECISION SUPPORT ONLY.

A transparent, additive rule score: each signal contributes capped points
and a human-readable reason with the evidence count. There is no hidden
model, so every point can be explained to an official and to the
beneficiary. A score must never be used to deny rations automatically; it
only prioritises what a human should look at.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .domain import RATION_TYPES, TokenStatus, VerificationAction, unit_for
from .i18n import reason

LEVELS = [(80, "CRITICAL"), (60, "HIGH"), (30, "MEDIUM"), (0, "LOW")]


@dataclass(frozen=True)
class Signal:
    code: str
    points_each: int
    cap: int


TOKEN_REUSE = Signal("RISK_TOKEN_REUSE", 15, 30)
BLOCKED = Signal("RISK_BLOCKED_VERIFICATION", 8, 24)
REJECTED = Signal("RISK_COLLECTION_REJECTED", 5, 15)
RAPID = Signal("RISK_RAPID_CLAIMS", 20, 30)
OVER_ENTITLEMENT = Signal("RISK_OVER_ENTITLEMENT", 25, 25)
OTHER_SHOP = Signal("RISK_OTHER_SHOP", 10, 20)
CANCELLATIONS = Signal("RISK_CANCELLATIONS", 5, 15)
CANCELLATION_ALLOWANCE = 2  # a couple of cancellations a month is normal


def _is_stock_reason(event: dict) -> bool:
    text = (event.get("reason") or "").lower()
    return "stock" in text or "inventory" in text


def level_for(score: int) -> str:
    return next(label for threshold, label in LEVELS if score >= threshold)


def score_beneficiaries(
    beneficiaries: list[dict],
    events: list[dict],
    collections: list[dict],
    tokens: list[dict],
    now: datetime,
    lang: str,
) -> list[dict]:
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    results = []

    for b in beneficiaries:
        mine = [e for e in events if e["beneficiary_id"] == b["id"]]
        signals: list[tuple[Signal, int, dict]] = []

        reuse = sum(1 for e in mine if e["action"] == VerificationAction.TOKEN_ALREADY_USED)
        # Scanning a used token logs BOTH TokenAlreadyUsed and a blocked
        # verification — don't count the same attempt twice.
        blocked = max(0, sum(1 for e in mine if e["action"] == VerificationAction.BENEFICIARY_VERIFIED and e["status"] in ("BLOCKED", "FAILED")) - reuse)
        # A rejection because the SHOP ran out of stock says nothing about the beneficiary.
        rejected = sum(1 for e in mine if e["action"] == VerificationAction.COLLECTION_REJECTED and not _is_stock_reason(e))
        signals += [(TOKEN_REUSE, reuse, {}), (BLOCKED, blocked, {}), (REJECTED, rejected, {})]

        visits = sorted({(c["at"], c["shop_id"]) for c in collections if c["beneficiary_id"] == b["id"]})
        rapid = sum(1 for (a, _), (c, _) in zip(visits, visits[1:]) if c - a < timedelta(hours=24))
        other_shop = sum(1 for _, shop in visits if shop != b["assigned_shop_id"])
        signals += [(RAPID, rapid, {}), (OTHER_SHOP, other_shop, {})]

        cancelled = sum(1 for t in tokens if t["user_id"] == b["user_id"] and t["status"] == TokenStatus.CANCELLED)
        signals.append((CANCELLATIONS, max(0, cancelled - CANCELLATION_ALLOWANCE), {"count": cancelled}))

        this_month: dict[int, float] = {}
        for c in collections:
            if c["beneficiary_id"] == b["id"] and c["at"] >= month_start:
                this_month[c["ration_type"]] = this_month.get(c["ration_type"], 0.0) + c["quantity"]
        for rtype, collected in this_month.items():
            entitled = b["monthly_entitlement"].get(rtype)
            if entitled is not None and collected > entitled + 1e-9:
                name = RATION_TYPES.get(rtype, str(rtype))
                unit = unit_for(name)
                signals.append((OVER_ENTITLEMENT, 1, {"collected": f"{collected:g} {unit}", "item": name, "entitled": f"{entitled:g} {unit}"}))

        score, reasons = 0, []
        for signal, count, params in signals:
            if count <= 0:
                continue
            points = min(signal.cap, signal.points_each * count)
            score += points
            reasons.append({**reason(signal.code, lang, **({"count": count} | params)), "points": points})

        if score > 0:
            score = min(100, score)
            results.append({
                "beneficiary_id": b["id"],
                "beneficiary_code": b["code"],
                "assigned_shop_id": b["assigned_shop_id"],
                "risk_score": score,
                "risk_level": level_for(score),
                "reasons": sorted(reasons, key=lambda r: -r["points"]),
            })

    return sorted(results, key=lambda r: -r["risk_score"])
