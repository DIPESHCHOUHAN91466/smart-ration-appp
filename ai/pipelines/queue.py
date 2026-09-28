"""Queue analytics from real token and collection timestamps.

Average service time is MEASURED: the gap between consecutive collections at
the same shop on the same day, keeping only gaps up to MAX_BUSY_GAP (longer
gaps mean the counter was idle, not serving). The median is used so a few
slow transactions don't skew it. With too few samples, the configured
default is used and flagged as such.
"""

from __future__ import annotations

import statistics
from datetime import UTC, datetime, timedelta

from ai.domain import TokenStatus
from ai.postprocessing.i18n import reason

MAX_BUSY_GAP_MINUTES = 20


def measured_service_minutes(collection_times: list[datetime]) -> list[float]:
    by_day: dict = {}
    for at in sorted(collection_times):
        by_day.setdefault(at.date(), []).append(at)
    gaps = []
    for times in by_day.values():
        for a, b in zip(times, times[1:], strict=False):
            minutes = (b - a).total_seconds() / 60
            if 0 < minutes <= MAX_BUSY_GAP_MINUTES:
                gaps.append(minutes)
    return gaps


def analyse_shop(
    shop: dict,
    todays_tokens: list[dict],
    recent_tokens: list[dict],
    collection_times: list[datetime],
    now_local: datetime,
    default_service_minutes: float,
    min_samples: int,
    lang: str,
) -> dict:
    gaps = measured_service_minutes(collection_times)
    if len(gaps) >= min_samples:
        service = statistics.median(gaps)
        source, note = "MEASURED", reason("QUEUE_MEASURED", lang, samples=len(gaps))
    else:
        service = default_service_minutes
        source, note = "DEFAULT", reason("QUEUE_DEFAULT", lang, minutes=default_service_minutes)

    open_statuses = (TokenStatus.PENDING, TokenStatus.CONFIRMED)
    served = [t for t in todays_tokens if t["status"] == TokenStatus.COMPLETED]
    waiting = [t for t in todays_tokens if t["status"] in open_statuses]
    # "In the queue now": due (slot started) but not yet served.
    due = [t for t in waiting if datetime.combine(t["slot_date"], t["start"]) <= now_local]
    delayed = [t for t in waiting if datetime.combine(t["slot_date"], t["end"]) < now_local]

    today = now_local.date()
    past = [t for t in recent_tokens if t["slot_date"] < today]
    no_show = [t for t in past if t["status"] in open_statuses or t["status"] == TokenStatus.NO_SHOW]
    booked_past = [t for t in past if t["status"] != TokenStatus.CANCELLED]

    return {
        "shop_id": shop["Id"],
        "shop_name": shop["ShopName"],
        "tokens_today": len(todays_tokens),
        "served_today": len(served),
        "waiting_today": len(waiting),
        "current_queue": len(due),
        "delayed_tokens": len(delayed),
        "avg_service_minutes": round(service, 1),
        "service_time_source": source,
        "service_time_samples": len(gaps),
        "estimated_wait_minutes": round(len(due) * service),
        "no_show_last_7_days": len(no_show),
        "no_show_rate": round(len(no_show) / len(booked_past), 3) if booked_past else None,
        "notes": [note],
    }


def local_now(utc_offset_minutes: int, now_utc: datetime | None = None) -> datetime:
    return (now_utc or utc_now()) + timedelta(minutes=utc_offset_minutes)


def utc_now() -> datetime:
    """Naive UTC, matching how the .NET API stores timestamps."""
    return datetime.now(UTC).replace(tzinfo=None)
