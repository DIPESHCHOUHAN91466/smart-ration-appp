"""Glue between the repository (data) and the pure analytics modules."""

from __future__ import annotations

from datetime import datetime, timedelta

from . import alerts, forecasting, inventory, queue, risk, shop_monitor
from .config import Settings
from .domain import RATION_TYPES, unit_for
from .i18n import reason
from .queue import local_now, utc_now
from .repository import Repository

FORECAST_LOOKBACK_DAYS = 180


class AnalyticsService:
    def __init__(self, repo: Repository, settings: Settings, clock=utc_now):
        self.repo = repo
        self.s = settings
        self.clock = clock  # injectable for tests

    # ---- forecasting ------------------------------------------------------

    def forecast(self, shop_id: int | None, horizon_days: int, lang: str) -> dict:
        now = self.clock()
        items, start, end = self._forecast_items(shop_id, horizon_days, lang, now)
        return {
            "shop_id": shop_id,
            "generated_at": now.isoformat() + "Z",
            "history_start": start.isoformat(),
            "history_end": end.isoformat(),
            "items": items,
        }

    def _forecast_items(self, shop_id, horizon_days, lang, now, distributed=None):
        today = now.date()
        first = self.repo.first_distribution_at(shop_id)
        start = max(first.date(), today - timedelta(days=FORECAST_LOOKBACK_DAYS)) if first else today
        if distributed is None:
            distributed = self.repo.distributed_items(datetime.combine(start, datetime.min.time()), shop_id)
        rows = [r for r in distributed if shop_id is None or r["shop_id"] == shop_id]
        # Today is incomplete: forecast from full days only.
        end = today - timedelta(days=1)
        minimum = self.s.forecast_min_history_days

        results = []
        for rtype, name in RATION_TYPES.items():
            events = [(r["at"].date(), r["quantity"]) for r in rows if r["ration_type"] == rtype]
            series = forecasting.daily_series(events, start, end) if end >= start else []
            f = forecasting.forecast(series, horizon_days, minimum)
            entry = {
                "ration_type": name,
                "unit": unit_for(name),
                "history_days": f.history_days,
                "horizon_days": horizon_days,
                "sufficient_data": f.sufficient,
                # Data-quality contract: never a number without its basis.
                "data_points": f.history_days,
                "minimum_required": minimum,
                "data_sufficient": f.sufficient,
                "data_quality": f.data_quality,
                "forecast": f.forecast_total,
                "confidence": f.confidence,
                "limitations": [],
            }
            if f.sufficient:
                entry |= {
                    "method": f.method,
                    "daily_rate": f.daily_rate,
                    "forecast_total": f.forecast_total,
                    "range_low": f.range_low,
                    "range_high": f.range_high,
                    "backtest_wmape": f.backtest_wmape,
                    "outlier_days": f.outlier_days,
                    "explanation": reason("FORECAST_METHOD", lang, days=f.history_days, method=f.method),
                }
                if f.outlier_days:
                    entry["limitations"].append(reason("FORECAST_ANOMALOUS", lang, count=f.outlier_days))
                if f.history_days < 60:
                    entry["limitations"].append(reason("LIMIT_SHORT_HISTORY", lang))
                entry["limitations"].append(reason("LIMIT_NO_SEASONALITY", lang))
            else:
                insufficient = reason("FORECAST_INSUFFICIENT_DATA", lang, days=f.history_days, required=minimum)
                entry["explanation"] = insufficient
                entry["limitations"].append(insufficient)
            results.append(entry)
        return results, start, end

    # ---- inventory ----------------------------------------------------------

    def inventory(self, shop_id: int | None, lang: str) -> dict:
        now = self.clock()
        window = self.s.analysis_window_days
        since = now - timedelta(days=window)
        rows = inventory.analyse(
            self.repo.inventory(shop_id),
            self.repo.distributed_items(since, shop_id),
            self.repo.movements(since, shop_id),
            self.repo.reserved_items(local_now(self.s.shop_utc_offset_minutes, now).date(), shop_id),
            window,
            inventory.Thresholds(self.s.low_stock_days, self.s.critical_stock_days),
            lang,
        )
        return {"window_days": window, "ledger_available": self.repo.has_table("InventoryMovements"), "items": rows}

    # ---- queue ----------------------------------------------------------------

    def queue(self, shop_id: int | None, lang: str) -> dict:
        now = self.clock()
        now_local = local_now(self.s.shop_utc_offset_minutes, now)
        today = now_local.date()
        tokens = self.repo.tokens(today - timedelta(days=7), today, shop_id)
        collections = self.repo.distributed_items(now - timedelta(days=self.s.analysis_window_days), shop_id)

        shops = []
        for shop in self.repo.shops(shop_id):
            sid = shop["Id"]
            mine = [t for t in tokens if t["shop_id"] == sid]
            # One timestamp per collection (items share it).
            times = sorted({r["at"] for r in collections if r["shop_id"] == sid})
            shops.append(queue.analyse_shop(
                shop, [t for t in mine if t["slot_date"] == today], mine, times, now_local,
                self.s.default_service_minutes, self.s.min_service_samples, lang))
        return {"local_time": now_local.isoformat(timespec="minutes"), "shops": shops}

    # ---- risk -----------------------------------------------------------------

    def risk(self, shop_id: int | None, limit: int, lang: str) -> dict:
        now = self.clock()
        since = now - timedelta(days=self.s.analysis_window_days)
        events = self.repo.verification_events(since)
        collections = [c for c in self.repo.distributed_items(since) if c["beneficiary_id"] is not None]
        tokens = self.repo.tokens(since.date(), (now + timedelta(days=30)).date())

        user_to_beneficiary = self.repo.beneficiary_ids_for_users(list({t["user_id"] for t in tokens}))
        candidate_ids = (
            {e["beneficiary_id"] for e in events if e["beneficiary_id"] is not None}
            | {c["beneficiary_id"] for c in collections}
            | set(user_to_beneficiary.values())
        )
        beneficiaries = self.repo.beneficiaries(sorted(candidate_ids))
        if shop_id is not None:
            beneficiaries = [b for b in beneficiaries if b["assigned_shop_id"] == shop_id]

        scored = risk.score_beneficiaries(beneficiaries, events, collections, tokens, now, lang)
        return {
            "window_days": self.s.analysis_window_days,
            "evaluated": len(beneficiaries),
            "flagged": len(scored),
            "disclaimer": reason("RISK_DISCLAIMER", lang),
            "items": scored[:limit],
        }

    # ---- shop monitoring ---------------------------------------------------------

    def shops(self, shop_id: int | None, lang: str) -> dict:
        now = self.clock()
        window = self.s.analysis_window_days
        since = now - timedelta(days=window)
        today = local_now(self.s.shop_utc_offset_minutes, now).date()
        results = shop_monitor.analyse(
            self.repo.shops(shop_id),
            self.repo.tokens(since.date(), today, shop_id),
            self.repo.booked_items_collected(since, shop_id),
            self.repo.distributed_items(since, shop_id),
            self.repo.verification_events(since, shop_id),
            self.repo.movements(since - timedelta(days=365), shop_id),
            self.repo.inventory(shop_id),
            today,
            lang,
            window_start=since,
        )
        return {"window_days": window, "shops": results}

    # ---- alerts ---------------------------------------------------------------

    def alerts(self, lang: str) -> dict:
        """Alert candidates for all shops; the .NET API persists + deduplicates them."""
        now = self.clock()
        today = now.date()
        lookback = datetime.combine(today - timedelta(days=FORECAST_LOOKBACK_DAYS), datetime.min.time())
        distributed = self.repo.distributed_items(lookback)

        inv = self.inventory(None, lang)["items"]
        candidates = alerts.low_stock(inv, lang)
        for shop in self.repo.shops():
            sid = shop["Id"]
            forecast_items, _, _ = self._forecast_items(sid, 7, lang, now, distributed)
            candidates += alerts.forecast_risk(sid, forecast_items, inv, lang)
            candidates += alerts.demand_spike(sid, distributed, today, lang)
        candidates += alerts.from_shop_findings(self.shops(None, lang)["shops"], lang)

        return {"generated_at": now.isoformat() + "Z", "count": len(candidates), "items": candidates}
