"""Shop-level monitoring: stock reconciliation, fulfilment, verification failures.

Checks, per shop over the analysis window:
  * Ledger reconciliation — each movement's BalanceAfter must equal the
    previous balance plus the signed movement (a break means stock changed
    outside the ledger), and the last ledger balance must match the current
    Inventory balance.
  * Fulfilment — items issued vs items booked on completed tokens.
  * Damage rate — damaged vs received.
  * Verification failure rate and no-show rate.
Status: OK, WATCH or INVESTIGATE. Findings are prompts for a human audit,
not conclusions.
"""

from __future__ import annotations

from ai.domain import RATION_TYPES, MovementType, TokenStatus, VerificationAction, unit_for
from ai.postprocessing.i18n import reason

TOLERANCE = 0.01
FAILED_RATE_WATCH, FAILED_RATE_INVESTIGATE = 0.15, 0.30
NO_SHOW_WATCH = 0.30
UNDER_ISSUE_WATCH = 0.80
DAMAGE_WATCH = 0.05
MIN_VERIFICATIONS = 5


def _signed(m: dict) -> float:
    if m["type"] in (MovementType.RECEIVED, MovementType.ADJUSTMENT):
        return m["quantity"]
    return -m["quantity"]


def reconcile(movements: list[dict], inventory: list[dict], lang: str) -> list[dict]:
    findings = []
    current = {(i["shop_id"], i["ration_type"]): i["available"] for i in inventory}
    by_item: dict[tuple, list[dict]] = {}
    for m in movements:
        by_item.setdefault((m["shop_id"], m["ration_type"]), []).append(m)

    for key, rows in by_item.items():
        # Chronological, id as tie-break: imported history has later ids than
        # live rows but earlier timestamps.
        rows.sort(key=lambda m: (m["at"], m["id"]))
        name = RATION_TYPES.get(key[1], str(key[1]))
        unit = unit_for(name)
        gaps = sum(1 for a, b in zip(rows, rows[1:], strict=False) if abs(a["balance_after"] + _signed(b) - b["balance_after"]) > TOLERANCE)
        if gaps:
            findings.append({"shop_id": key[0], "severity": "INVESTIGATE", **reason("SHOP_LEDGER_GAP", lang, item=name, count=gaps)})
        expected = rows[-1]["balance_after"]
        actual = current.get(key)
        if actual is not None and abs(actual - expected) > TOLERANCE:
            findings.append({"shop_id": key[0], "severity": "INVESTIGATE", **reason(
                "SHOP_LEDGER_MISMATCH", lang, item=name, actual=f"{actual:g} {unit}",
                expected=f"{expected:g} {unit}", variance=f"{actual - expected:+g} {unit}")})
    return findings


def analyse(
    shops: list[dict],
    tokens: list[dict],
    token_items_booked: dict[tuple, float],
    distributed: list[dict],
    events: list[dict],
    movements: list[dict],
    inventory: list[dict],
    today,
    lang: str,
    window_start=None,
) -> list[dict]:
    ledger_findings = reconcile(movements, inventory, lang)
    results = []

    for shop in shops:
        sid = shop["Id"]
        findings = [f for f in ledger_findings if f["shop_id"] == sid]

        verifications = [e for e in events if e["shop_id"] == sid and e["action"] == VerificationAction.BENEFICIARY_VERIFIED]
        failed = sum(1 for e in verifications if e["status"] in ("FAILED", "BLOCKED"))
        failed_rate = failed / len(verifications) if verifications else 0.0
        if len(verifications) >= MIN_VERIFICATIONS and failed_rate >= FAILED_RATE_WATCH:
            findings.append({"shop_id": sid, "severity": "INVESTIGATE" if failed_rate >= FAILED_RATE_INVESTIGATE else "WATCH",
                             **reason("SHOP_HIGH_FAILED_VERIFICATION", lang, failed=failed, total=len(verifications), rate=round(failed_rate * 100))})

        mine = [t for t in tokens if t["shop_id"] == sid]
        past = [t for t in mine if t["slot_date"] < today and t["status"] != TokenStatus.CANCELLED]
        no_show = [t for t in past if t["status"] in (TokenStatus.PENDING, TokenStatus.CONFIRMED, TokenStatus.NO_SHOW)]
        no_show_rate = len(no_show) / len(past) if past else 0.0
        if len(past) >= MIN_VERIFICATIONS and no_show_rate >= NO_SHOW_WATCH:
            findings.append({"shop_id": sid, "severity": "WATCH", **reason("SHOP_HIGH_NO_SHOW", lang, count=len(no_show), rate=round(no_show_rate * 100))})

        issued: dict[int, float] = {}
        for d in distributed:
            if d["shop_id"] == sid:
                issued[d["ration_type"]] = issued.get(d["ration_type"], 0.0) + d["quantity"]
        fulfilment = []
        for (shop_id, rtype), booked in token_items_booked.items():
            if shop_id != sid or booked <= 0:
                continue
            name = RATION_TYPES.get(rtype, str(rtype))
            unit = unit_for(name)
            got = issued.get(rtype, 0.0)
            rate = got / booked
            fulfilment.append({"ration_type": name, "unit": unit, "booked": round(booked, 2), "issued": round(got, 2), "fulfilment_rate": round(rate, 3)})
            if rate < UNDER_ISSUE_WATCH:
                findings.append({"shop_id": sid, "severity": "WATCH", **reason(
                    "SHOP_UNDER_ISSUE", lang, item=name, issued=f"{got:g} {unit}", booked=f"{booked:g} {unit}", rate=round(rate * 100))})

        # Damage rate in the analysis window, relative to the stock actually
        # handled there (balance at window start + receipts), so it isn't
        # diluted or hidden by the timing of deliveries.
        by_type: dict[int, list[dict]] = {}
        for m in movements:
            if m["shop_id"] == sid:
                by_type.setdefault(m["ration_type"], []).append(m)
        for rtype, rows in by_type.items():
            rows.sort(key=lambda m: (m["at"], m["id"]))
            before = [m for m in rows if window_start is not None and m["at"] < window_start]
            inside = [m for m in rows if window_start is None or m["at"] >= window_start]
            opening = before[-1]["balance_after"] if before else 0.0
            received = sum(m["quantity"] for m in inside if m["type"] == MovementType.RECEIVED)
            damaged = sum(m["quantity"] for m in inside if m["type"] == MovementType.DAMAGED)
            handled = opening + received
            if handled > 0 and damaged / handled >= DAMAGE_WATCH:
                name = RATION_TYPES.get(rtype, str(rtype))
                findings.append({"shop_id": sid, "severity": "WATCH", **reason(
                    "SHOP_HIGH_DAMAGE", lang, item=name, damaged=f"{damaged:g} {unit_for(name)}", rate=round(damaged / handled * 100))})

        status = "INVESTIGATE" if any(f["severity"] == "INVESTIGATE" for f in findings) else "WATCH" if findings else "OK"
        results.append({
            "shop_id": sid,
            "shop_name": shop["ShopName"],
            "status": status,
            "verifications": len(verifications),
            "failed_verifications": failed,
            "failed_verification_rate": round(failed_rate, 3),
            "tokens_in_window": len(mine),
            "cancelled_tokens": sum(1 for t in mine if t["status"] == TokenStatus.CANCELLED),
            "no_show_tokens": len(no_show),
            "fulfilment": fulfilment,
            "findings": [{k: v for k, v in f.items() if k != "shop_id"} for f in findings],
        })

    order = {"INVESTIGATE": 0, "WATCH": 1, "OK": 2}
    return sorted(results, key=lambda r: (order[r["status"]], r["shop_id"]))
