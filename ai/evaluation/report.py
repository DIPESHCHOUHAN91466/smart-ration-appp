"""Forecast accuracy report: for every shop and item, which model was selected, how well it backtested,
and how much history it had. This is the model-monitoring view — run it after new history arrives or
before changing a model, and compare `model_version` between runs.

    (from the repository root)
    ai\\.venv\\Scripts\\python -m ai.evaluation.report                  # all active shops, 7-day horizon
    ai\\.venv\\Scripts\\python -m ai.evaluation.report --shop 3 --json  # one shop, machine-readable

Read-only (SMARTRATION_AI_DB_URL, the same read-only account as the service). Exit code 0 always when the
database is reachable: a weak forecast is information, not an error; 2 if the database can't be read.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass

from ai.configs.settings import Settings, load_settings
from ai.errors import AIServiceError
from ai.inference.service import AnalyticsService
from ai.models.forecasting import MODEL_VERSION
from ai.preprocessing.repository import Repository, create_db_engine


@dataclass(frozen=True)
class AccuracyRow:
    shop_id: int
    shop: str
    item: str
    sufficient_data: bool
    history_days: int
    method: str | None
    backtest_wmape: float | None
    confidence: str | None
    data_quality: str


@dataclass(frozen=True)
class AccuracySummary:
    model_version: str
    horizon_days: int
    forecasts: int
    insufficient: int
    median_wmape: float | None
    confidence_counts: dict[str, int]
    method_counts: dict[str, int]


def evaluate(service: AnalyticsService, repo: Repository, horizon_days: int, shop_id: int | None = None) -> list[AccuracyRow]:
    rows = []
    for shop in repo.shops(shop_id):
        result = service.forecast(shop["Id"], horizon_days, "en")
        for item in result["items"]:
            rows.append(AccuracyRow(
                shop_id=shop["Id"], shop=shop["ShopName"], item=item["ration_type"], sufficient_data=item["sufficient_data"],
                history_days=item["history_days"], method=item.get("method"), backtest_wmape=item.get("backtest_wmape"),
                confidence=item.get("confidence"), data_quality=item["data_quality"],
            ))
    return rows


def summarize(rows: list[AccuracyRow], horizon_days: int) -> AccuracySummary:
    usable = [r for r in rows if r.sufficient_data]
    errors = sorted(r.backtest_wmape for r in usable if r.backtest_wmape is not None)
    median = errors[len(errors) // 2] if errors else None
    confidence_counts: dict[str, int] = {}
    method_counts: dict[str, int] = {}
    for r in usable:
        confidence_counts[r.confidence or "NONE"] = confidence_counts.get(r.confidence or "NONE", 0) + 1
        method_counts[r.method or "NONE"] = method_counts.get(r.method or "NONE", 0) + 1
    return AccuracySummary(MODEL_VERSION, horizon_days, len(usable), len(rows) - len(usable), median, confidence_counts, method_counts)


def main(argv: list[str] | None = None, settings: Settings | None = None) -> int:
    parser = argparse.ArgumentParser(description="Forecast accuracy per shop and item (read-only).")
    parser.add_argument("--shop", type=int, default=None, help="one shop id (default: every active shop)")
    parser.add_argument("--horizon", type=int, default=7, help="forecast horizon in days (default 7)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    args = parser.parse_args(argv)
    if args.horizon < 1:
        parser.error("--horizon must be 1 or more")

    settings = settings or load_settings()
    repo = Repository(create_db_engine(settings.db_url))
    try:
        rows = evaluate(AnalyticsService(repo, settings), repo, args.horizon, args.shop)
    except AIServiceError as exc:
        print(f"Cannot read the database: {exc.error_code}", file=sys.stderr)
        return 2
    summary = summarize(rows, args.horizon)

    if args.json:
        print(json.dumps({"summary": asdict(summary), "rows": [asdict(r) for r in rows]}, indent=2, ensure_ascii=False))
        return 0
    print(f"Forecast accuracy — model {summary.model_version}, {summary.horizon_days}-day horizon")
    print(f"{'shop':<28} {'item':<12} {'days':>5} {'method':<32} {'wMAPE':>6} confidence")
    for r in rows:
        wmape = f"{r.backtest_wmape:.3f}" if r.backtest_wmape is not None else "-"
        method = r.method or "(not enough history)"
        print(f"{r.shop[:28]:<28} {r.item:<12} {r.history_days:>5} {method:<32} {wmape:>6} {r.confidence or '-'}")
    median = f"{summary.median_wmape:.3f}" if summary.median_wmape is not None else "-"
    print(f"\n{summary.forecasts} forecasts, {summary.insufficient} without enough history; median wMAPE {median}; "
          f"confidence {summary.confidence_counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
