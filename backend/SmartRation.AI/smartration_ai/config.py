"""Configuration from environment variables (optionally a local, git-ignored .env).

Nothing secret has a default: the service refuses to start without a database
URL and an API key.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# .env next to the service folder (backend/SmartRation.AI/.env), never committed.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw not in (None, "") else default


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    # SQLAlchemy URL, e.g. mysql+pymysql://smartration_ai:***@localhost/smartration
    # or sqlite:///C:/path/to/smartration.db. Use a READ-ONLY account.
    db_url: str
    # Shared secret the .NET API sends in X-Api-Key.
    api_key: str
    # Shops record slot times in local time; stored timestamps are UTC.
    shop_utc_offset_minutes: int
    # Forecasting
    forecast_min_history_days: int
    forecast_default_horizon_days: int
    # Inventory thresholds, in days of stock remaining at current usage.
    low_stock_days: float
    critical_stock_days: float
    # Queue: used only until enough measured service times exist.
    default_service_minutes: float
    min_service_samples: int
    # Analysis window for risk scoring and shop monitoring.
    analysis_window_days: int
    log_level: str


def load_settings() -> Settings:
    db_url = os.getenv("SMARTRATION_AI_DB_URL", "").strip()
    api_key = os.getenv("SMARTRATION_AI_API_KEY", "").strip()
    if not db_url:
        raise RuntimeError("SMARTRATION_AI_DB_URL is not set (see .env.example).")
    if len(api_key) < 24:
        raise RuntimeError("SMARTRATION_AI_API_KEY must be set to a random value of at least 24 characters.")

    return Settings(
        db_url=db_url,
        api_key=api_key,
        shop_utc_offset_minutes=_int("SHOP_UTC_OFFSET_MINUTES", 330),  # IST
        forecast_min_history_days=_int("FORECAST_MIN_HISTORY_DAYS", 14),
        forecast_default_horizon_days=_int("FORECAST_DAYS", 7),
        low_stock_days=_float("LOW_STOCK_DAYS", 7),
        critical_stock_days=_float("CRITICAL_STOCK_DAYS", 3),
        default_service_minutes=_float("DEFAULT_SERVICE_MINUTES", 4.0),
        min_service_samples=_int("MIN_SERVICE_SAMPLES", 5),
        analysis_window_days=_int("ANALYSIS_WINDOW_DAYS", 30),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
