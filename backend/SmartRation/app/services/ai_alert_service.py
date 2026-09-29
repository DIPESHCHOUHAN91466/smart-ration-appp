"""Persisted AI alerts (built-in rules + the optional Python AI service), in the AIAlerts table.

* Dedup: while an alert with the same DedupKey is Open/UnderReview, re-detection only refreshes it
  (LastSeenAt, score, text), so refreshing the dashboard never adds rows.
* Throttled: automatic syncs run at most once per 5 minutes (per API process); `force` skips that.
* Scoped: shop owners only ever see their own shop's alerts; citizens none.
* Alerts are review prompts, never proof of fraud — nothing here acts on them.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import BadRequest, Forbidden, NotFound
from app.database.enums import AIAlertSeverity, AIAlertStatus, RationType, UserRole, parse_enum
from app.database.models import AIAlert, RationShop
from app.services import audit_service
from app.services.ai_client import AiClient
from app.utils.dotnet import dt
from app.utils.time import utc_now

PYTHON_SOURCE = "PYTHON_AI"
SYNC_INTERVAL = timedelta(minutes=5)
ACTIVE = (int(AIAlertStatus.Open), int(AIAlertStatus.UnderReview))
NOTICE = "Decision support only — not proof of fraud. Review before acting."

_sync_lock = threading.Lock()
_last_sync: datetime | None = None


def _sync_result(**values: Any) -> dict:
    out = {"available": False, "skipped": False, "created": 0, "updated": 0, "rejected": 0, "lastAnalysisAt": None,
           "errorCode": None, "message": None}
    out.update(values)
    return out


def _truncate(value: Any, limit: int) -> str | None:
    return None if not isinstance(value, str) else value[:limit]


def _parse(item: Any) -> AIAlert | None:
    """Validates one candidate from the AI service; malformed entries are skipped, never trusted."""
    if not isinstance(item, dict):
        return None
    dedup, kind, severity_text = item.get("dedup_key"), item.get("alert_type"), item.get("severity")
    severity = parse_enum(AIAlertSeverity, severity_text) if isinstance(severity_text, str) else None
    if (not isinstance(dedup, str) or not dedup.strip() or len(dedup) > 128 or not isinstance(kind, str) or not kind.strip()
            or len(kind) > 64 or severity is None):
        return None
    shop = item.get("shop_id")
    rtype = item.get("ration_type")
    score = item.get("score")
    metadata = item.get("metadata")
    return AIAlert(
        Source=PYTHON_SOURCE, DedupKey=dedup, AlertType=kind, Severity=int(severity),
        ShopId=shop if isinstance(shop, int) and not isinstance(shop, bool) else None,
        RationType=rtype if isinstance(rtype, int) and not isinstance(rtype, bool) and rtype in RationType._value2member_map_ else None,
        Score=min(max(float(score), 0.0), 100.0) if isinstance(score, int | float) and not isinstance(score, bool) else None,
        Title=_truncate(item.get("title"), 200), Description=_truncate(item.get("description"), 2000) or "",
        RecommendedAction=_truncate(item.get("recommended_action"), 500),
        MetadataJson=_truncate(json.dumps(metadata, ensure_ascii=False, separators=(",", ":")), 4000) if isinstance(metadata, dict) else None,
        Status=int(AIAlertStatus.Open))


def sync_from_ai(db: Session, client: AiClient, actor: Actor, force: bool) -> dict:
    global _last_sync
    if not force and _last_sync is not None and utc_now() - _last_sync < SYNC_INTERVAL:
        return _sync_result(skipped=True, lastAnalysisAt=dt(_last_sync), message="Recently analysed.")
    with _sync_lock:   # two concurrent refreshes must not both insert the same alert
        result = client.get("/v1/alerts", {"lang": "en"})
        items = result.data.get("items") if result.available and isinstance(result.data, dict) else None
        if not isinstance(items, list):
            return _sync_result(lastAnalysisAt=dt(_last_sync), errorCode=result.error_code or "AI_MALFORMED_RESPONSE",
                                message=result.message or "The AI service returned no alert data.")
        now = utc_now()
        created = updated = rejected = 0
        for item in items:
            candidate = _parse(item)
            if candidate is None:
                rejected += 1
                continue
            existing = db.scalar(select(AIAlert).where(AIAlert.DedupKey == candidate.DedupKey, AIAlert.Status.in_(ACTIVE)).limit(1))
            if existing is not None:
                existing.LastSeenAt = now
                existing.Score = candidate.Score
                existing.Severity = max(existing.Severity, candidate.Severity)
                existing.Description = candidate.Description
                existing.MetadataJson = candidate.MetadataJson
                updated += 1
                continue
            candidate.DetectedAt = candidate.LastSeenAt = candidate.CreatedAt = now
            db.add(candidate)
            db.flush()   # a later item with the same key in this batch must see this one
            created += 1
        if created:
            audit_service.record(db, actor.user_id, "AI_ALERTS_CREATED", "AIAlert",
                                 details=f"created={created} updated={updated} source={PYTHON_SOURCE}", role=actor.role.name)
        db.commit()
        _last_sync = now
        return _sync_result(available=True, created=created, updated=updated, rejected=rejected, lastAnalysisAt=dt(now))


def _scoped(q: Select, actor: Actor) -> Select:
    if actor.role in (UserRole.GovernmentOfficial, UserRole.Admin):
        return q
    if actor.role == UserRole.ShopOwner and actor.ration_shop_id is not None:
        return q.where(AIAlert.ShopId == actor.ration_shop_id)   # never shop-less / system-wide alerts
    return q.where(AIAlert.Id.is_(None))


def _metadata(text: str | None) -> Any:
    if not text or not text.strip():
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def _dtos(db: Session, alerts: list[AIAlert]) -> list[dict]:
    ids = {a.ShopId for a in alerts if a.ShopId is not None}
    names = dict(db.execute(select(RationShop.Id, RationShop.ShopName).where(RationShop.Id.in_(ids))).tuples().all()) if ids else {}
    return [{"id": a.Id, "source": a.Source, "alertType": a.AlertType, "severity": AIAlertSeverity(a.Severity).name.upper(),
             "status": AIAlertStatus(a.Status).name, "shopId": a.ShopId, "shopName": names.get(a.ShopId) if a.ShopId is not None else None,
             "beneficiaryId": a.BeneficiaryId, "rationType": RationType(a.RationType).name if a.RationType is not None else None,
             "title": a.Title or a.AlertType, "description": a.Description, "score": a.Score, "recommendedAction": a.RecommendedAction,
             "metadata": _metadata(a.MetadataJson), "detectedAt": dt(a.DetectedAt or a.CreatedAt), "lastSeenAt": dt(a.LastSeenAt),
             "resolvedAt": dt(a.ResolvedAt), "resolutionNote": a.ResolutionNote, "notice": NOTICE} for a in alerts]


def list_alerts(db: Session, actor: Actor, status: str | None, shop_id: int | None, source: str | None, limit: int) -> list[dict]:
    q = _scoped(select(AIAlert), actor)
    if shop_id is not None:
        q = q.where(AIAlert.ShopId == shop_id)
    if source and source.strip():
        q = q.where(AIAlert.Source == source)
    key = (status or "").lower()
    if key == "active":
        q = q.where(AIAlert.Status.in_(ACTIVE))
    elif key not in ("", "all"):
        parsed = parse_enum(AIAlertStatus, status or "")
        if parsed is None:
            raise BadRequest("Unknown alert status filter.", "INVALID_STATUS")
        q = q.where(AIAlert.Status == int(parsed))
    rows = db.scalars(q.order_by(AIAlert.Severity.desc(), func.coalesce(AIAlert.LastSeenAt, AIAlert.CreatedAt).desc(), AIAlert.Id.desc())
                      .limit(min(max(limit, 1), 200))).all()
    return _dtos(db, list(rows))


def get_alert(db: Session, actor: Actor, alert_id: int) -> dict:
    alert = db.scalar(_scoped(select(AIAlert), actor).where(AIAlert.Id == alert_id))
    if alert is None:
        raise NotFound("Alert not found.")
    return _dtos(db, [alert])[0]


def resolve(db: Session, actor: Actor, alert_id: int, status_text: str, note: str | None) -> dict:
    if actor.role not in (UserRole.GovernmentOfficial, UserRole.Admin):
        raise Forbidden("Only government officials can resolve alerts.")
    status = parse_enum(AIAlertStatus, status_text)
    if status is None or status == AIAlertStatus.Open:
        raise BadRequest("Status must be UnderReview, Resolved or Dismissed.", "INVALID_STATUS")
    alert = db.get(AIAlert, alert_id)
    if alert is None:
        raise NotFound("Alert not found.")
    alert.Status = int(status)
    alert.ResolutionNote = note.strip() if note is not None else None
    if status in (AIAlertStatus.Resolved, AIAlertStatus.Dismissed):
        alert.ResolvedAt = utc_now()
        alert.ResolvedByUserId = actor.user_id
    audit_service.record(db, actor.user_id, f"AI_ALERT_{status.name.upper()}", "AIAlert", str(alert.Id),
                         f"{alert.AlertType} {alert.DedupKey or ''}", role=actor.role.name, ip_address=actor.ip_address)
    db.commit()
    return _dtos(db, [alert])[0]
