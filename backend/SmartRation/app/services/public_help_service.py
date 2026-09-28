"""Public facts for the Public Help assistant: active shops and scheme entitlements.

Only public, non-personal data is read here. Results are cached briefly so a busy chat doesn't
query MySQL for every message; the lists change rarely (shops, scheme configuration).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.repositories import bookings, catalog
from app.utils.time import utc_now

CACHE_SECONDS = 300
_cache: dict[str, tuple[float, list[dict]]] = {}
_lock = threading.Lock()


def _cached(key: str, load: Callable[[], list[dict]]) -> list[dict]:
    now = time.monotonic()
    with _lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_SECONDS:
            return hit[1]
    value = load()
    with _lock:
        _cache[key] = (now, value)
    return value


def clear_cache() -> None:
    with _lock:
        _cache.clear()


class DatabasePublicData:
    """Implements engine.PublicData on top of a request's database session."""

    def __init__(self, db: Session):
        self.db = db

    def shops(self) -> list[dict]:
        def load() -> list[dict]:
            rows = catalog.active_shops(self.db)
            return [{"name": s.ShopName, "address": s.Address, "village": s.Village, "taluka": s.Taluka, "district": s.District}
                    for s in rows]
        return _cached("shops", load)

    def schemes(self) -> list[dict]:
        def load() -> list[dict]:
            items = {i.RationType: i for i in catalog.active_items(self.db)}
            result = []
            for scheme in catalog.active_schemes(self.db):
                quotas = catalog.scheme_entitlements(self.db, scheme.Id)
                result.append({
                    "code": scheme.SchemeCode, "name": scheme.Name,
                    "items": [{"name": items[q.RationType].Name, "vernacular": items[q.RationType].VernacularName,
                               "unit": items[q.RationType].Unit, "quota": q.QuotaPerEligibleMemberPerMonth}
                              for q in quotas if q.RationType in items],
                })
            return result
        return _cached("schemes", load)


UPCOMING_STATUSES = {1: "Pending", 2: "Confirmed"}  # TokenStatus values still to be collected


class UserBookings:
    """Implements engine.PersonalData for ONE signed-in user: every query is filtered by that
    user's id, taken from their verified access token — never from the message text."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def upcoming_bookings(self, limit: int = 3) -> list[dict]:
        today = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        rows = bookings.upcoming_for_user(self.db, self.user_id, today, UPCOMING_STATUSES, limit)
        return [{"id": r.Id, "token": r.TokenNumber, "status": UPCOMING_STATUSES[r.Status], "shop": r.ShopName,
                 "date": r.SlotDate.strftime("%d-%m-%Y"), "start": r.StartTime.strftime("%H:%M"), "end": r.EndTime.strftime("%H:%M")}
                for r in rows]
