"""Public facts for the Public Help assistant: active shops and scheme entitlements.

Only public, non-personal data is read here. Results are cached briefly so a busy chat doesn't
query MySQL for every message; the lists change rarely (shops, scheme configuration).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RationItem, RationScheme, RationShop, SchemeEntitlementItem

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
            rows = self.db.scalars(select(RationShop).where(RationShop.IsActive.is_(True)).order_by(RationShop.ShopName)).all()
            return [{"name": s.ShopName, "address": s.Address, "village": s.Village, "taluka": s.Taluka, "district": s.District}
                    for s in rows]
        return _cached("shops", load)

    def schemes(self) -> list[dict]:
        def load() -> list[dict]:
            items = {i.RationType: i for i in self.db.scalars(select(RationItem).where(RationItem.IsActive.is_(True))).all()}
            result = []
            for scheme in self.db.scalars(select(RationScheme).where(RationScheme.IsActive.is_(True)).order_by(RationScheme.SchemeCode)).all():
                quotas = self.db.scalars(select(SchemeEntitlementItem).where(SchemeEntitlementItem.RationSchemeId == scheme.Id)
                                         .order_by(SchemeEntitlementItem.RationType)).all()
                result.append({
                    "code": scheme.SchemeCode, "name": scheme.Name,
                    "items": [{"name": items[q.RationType].Name, "vernacular": items[q.RationType].VernacularName,
                               "unit": items[q.RationType].Unit, "quota": q.QuotaPerEligibleMemberPerMonth}
                              for q in quotas if q.RationType in items],
                })
            return result
        return _cached("schemes", load)
