"""AI analytics, persisted alerts and optional document OCR.

Migrated from the C# AIController, AIAlertsController and OcrController. The Python AI service (ai/) is
optional: when it is down, forecast / inventory / queue answer from the built-in rules ("fallback"), and
everything else reports "unavailable" instead of failing. Shop owners are always scoped to their own shop;
citizens have no access (except the insight on their own beneficiary record).
OCR output is a suggestion for an operator to confirm — never identity verification; nothing is stored.
"""

from __future__ import annotations

import base64
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies.auth import OFFICIALS, STAFF, Actor, actor
from app.api.routes._common import json_body
from app.core.body import Body
from app.core.errors import BadRequest, Forbidden, ok
from app.database.connection import get_db
from app.database.enums import UserRole
from app.services import ai_alert_service, ai_rules_service, audit_service, profile_service
from app.services.ai_client import AiClient, AiResult

router = APIRouter(prefix="/api", tags=["ai"])
staff = actor(*STAFF)
officials = actor(*OFFICIALS)

OCR_MAX_BYTES = 5 * 1024 * 1024
OCR_TYPES = ("image/png", "image/jpeg")


def _client(request: Request) -> AiClient:
    return request.app.state.ai_api


def _scope(who: Actor, requested: int | None) -> int | None:
    return who.ration_shop_id if who.role == UserRole.ShopOwner else requested


def _query(shop_id: int | None, lang: str, **extra: str) -> dict[str, str | None]:
    return {"shop_id": str(shop_id) if shop_id is not None else None, "lang": lang if lang in ("hi", "mr") else "en", **extra}


def _dto(result: AiResult) -> dict:
    if result.available:
        return {"available": True, "source": "python-ai", "data": result.data, "fallback": None, "errorCode": None, "message": None}
    return {"available": False, "source": "unavailable", "data": None, "fallback": None, "errorCode": result.error_code, "message": result.message}


def _with_fallback(result: AiResult, fallback: Callable[[], Any]) -> dict:
    dto = _dto(result)
    if not dto["available"]:
        dto["source"] = "fallback"
        dto["fallback"] = fallback()
    return dto


# ---------------------------------------------------------------- built-in rules

@router.get("/ai/intelligence-center", summary="All rule-based analytics in one view (officials)")
def intelligence_center(_: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(ai_rules_service.intelligence_center(db))


@router.get("/ai/demand-forecast", summary="Trailing-30-day demand trend")
def demand_forecast(shopId: int | None = None, who: Actor = Depends(staff), db: Session = Depends(get_db)):
    return ok(ai_rules_service.demand_forecast(db, _scope(who, shopId)))


@router.get("/ai/inventory-risk", summary="Stock-cover risk per shop and item")
def inventory_risk(shopId: int | None = None, who: Actor = Depends(staff), db: Session = Depends(get_db)):
    return ok(ai_rules_service.inventory_risks(db, _scope(who, shopId)))


@router.get("/ai/queue-prediction", summary="Today's queue wait estimate")
def queue_prediction(shopId: int | None = None, who: Actor = Depends(staff), db: Session = Depends(get_db)):
    return ok(ai_rules_service.queue_predictions(db, _scope(who, shopId)))


@router.get("/ai/alerts", summary="Recent rule-based anomaly alerts (raw rows)")
def recent_alerts(who: Actor = Depends(staff), db: Session = Depends(get_db)):
    alerts = ai_rules_service.recent_alerts(db)
    if who.role == UserRole.ShopOwner:
        alerts = [a for a in alerts if a.ShopId == who.ration_shop_id]
    return ok([ai_rules_service.alert_entity(a) for a in alerts])


@router.get("/ai/shops/{shop_id}/insight", summary="One shop's risk summary")
def shop_insight(shop_id: int, who: Actor = Depends(staff), db: Session = Depends(get_db)):
    if who.role == UserRole.ShopOwner and who.ration_shop_id != shop_id:
        raise Forbidden("You can only view insights for your own shop.")
    return ok(ai_rules_service.shop_insight(db, shop_id))


@router.get("/ai/beneficiaries/{beneficiary_id}/insight", summary="One beneficiary's risk summary")
def beneficiary_insight(beneficiary_id: int, who: Actor = Depends(actor()), db: Session = Depends(get_db)):
    profile_service.ensure_can_see(db, who, beneficiary_id)
    return ok(ai_rules_service.beneficiary_insight(db, beneficiary_id))


# ---------------------------------------------------------------- Python AI service analytics

@router.get("/ai/analytics/forecast", summary="AI demand forecast (falls back to the built-in trend)")
def analytics_forecast(request: Request, shopId: int | None = None, horizonDays: int = 7, lang: str = "en",
                       who: Actor = Depends(staff), db: Session = Depends(get_db)):
    scope = _scope(who, shopId)
    result = _client(request).get("/v1/forecast", _query(scope, lang, horizon_days=str(min(max(horizonDays, 1), 90))))
    return ok(_with_fallback(result, lambda: ai_rules_service.demand_forecast(db, scope)))


@router.get("/ai/analytics/inventory", summary="AI inventory analytics (falls back to built-in stock risk)")
def analytics_inventory(request: Request, shopId: int | None = None, lang: str = "en", who: Actor = Depends(staff), db: Session = Depends(get_db)):
    scope = _scope(who, shopId)
    return ok(_with_fallback(_client(request).get("/v1/inventory", _query(scope, lang)), lambda: ai_rules_service.inventory_risks(db, scope)))


@router.get("/ai/analytics/queue", summary="AI queue analytics (falls back to the built-in estimate)")
def analytics_queue(request: Request, shopId: int | None = None, lang: str = "en", who: Actor = Depends(staff), db: Session = Depends(get_db)):
    scope = _scope(who, shopId)
    return ok(_with_fallback(_client(request).get("/v1/queue", _query(scope, lang)), lambda: ai_rules_service.queue_predictions(db, scope)))


@router.get("/ai/analytics/risk", summary="AI beneficiary risk ranking (officials)")
def analytics_risk(request: Request, shopId: int | None = None, limit: int = 25, lang: str = "en", _: Actor = Depends(officials)):
    return ok(_dto(_client(request).get("/v1/risk/beneficiaries", _query(shopId, lang, limit=str(min(max(limit, 1), 200))))))


@router.get("/ai/analytics/shops", summary="AI shop monitor")
def analytics_shops(request: Request, shopId: int | None = None, lang: str = "en", who: Actor = Depends(staff)):
    return ok(_dto(_client(request).get("/v1/shops/monitor", _query(_scope(who, shopId), lang))))


# ---------------------------------------------------------------- persisted alerts

@router.get("/ai/alerts/list", summary="Alerts (filterable by status / shop / source)")
def alerts_list(status: str | None = None, shopId: int | None = None, source: str | None = None, limit: int = 100,
                who: Actor = Depends(staff), db: Session = Depends(get_db)):
    return ok(ai_alert_service.list_alerts(db, who, status, shopId, source, limit))


@router.get("/ai/alerts/active", summary="Open + under-review alerts (runs a throttled refresh first)")
def alerts_active(request: Request, shopId: int | None = None, who: Actor = Depends(staff), db: Session = Depends(get_db)):
    sync = ai_alert_service.sync_from_ai(db, _client(request), who, force=False)
    return ok({"sync": sync, "items": ai_alert_service.list_alerts(db, who, "active", shopId, None, 200)})


@router.get("/ai/alerts/shop/{shop_id}", summary="One shop's alerts")
def alerts_for_shop(shop_id: int, status: str | None = "active", who: Actor = Depends(staff), db: Session = Depends(get_db)):
    if who.role == UserRole.ShopOwner and who.ration_shop_id != shop_id:
        raise Forbidden("You can only view alerts for your own shop.")
    return ok(ai_alert_service.list_alerts(db, who, status, shop_id, None, 200))


@router.get("/ai/alerts/{alert_id}", summary="One alert")
def alert_detail(alert_id: int, who: Actor = Depends(staff), db: Session = Depends(get_db)):
    return ok(ai_alert_service.get_alert(db, who, alert_id))


@router.post("/ai/alerts/{alert_id}/resolve", summary="Mark an alert under review / resolved / dismissed (officials)")
def alert_resolve(alert_id: int, body: Body = Depends(json_body), who: Actor = Depends(officials), db: Session = Depends(get_db)):
    status = body.string("Status", required=True)
    if status and status not in ("UnderReview", "Resolved", "Dismissed"):
        body.errors.append("Status: Status must be UnderReview, Resolved or Dismissed.")
    note = body.string("Note", max_length=500)
    body.raise_if_invalid()
    return ok(ai_alert_service.resolve(db, who, alert_id, status, note), "Alert updated")


@router.post("/ai/alerts/sync", summary="Re-analyse now (still deduplicated; officials)")
def alerts_sync(request: Request, who: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(ai_alert_service.sync_from_ai(db, _client(request), who, force=True))


# ---------------------------------------------------------------- optional OCR

@router.post("/ocr/extract", summary="Suggest fields from a ration-card photo (PNG/JPEG, 5 MB; nothing stored)")
def ocr_extract(request: Request, file: UploadFile | None = File(default=None), who: Actor = Depends(staff), db: Session = Depends(get_db)):
    data = file.file.read(OCR_MAX_BYTES + 1) if file is not None else b""
    if file is None or not data or len(data) > OCR_MAX_BYTES or file.content_type not in OCR_TYPES:
        raise BadRequest("Upload a PNG or JPEG image up to 5 MB.", "INVALID_IMAGE")
    result = _client(request).post("/v1/ocr/extract", {"image_base64": base64.b64encode(data).decode("ascii")})
    audit_service.record(db, who.user_id, "OCR_EXTRACT", "Document", details=f"bytes={len(data)}",
                         result="SUCCESS" if result.available else "FAILED", role=who.role.name, ip_address=who.ip_address)
    db.commit()
    return ok(_dto(result))


@router.post("/ocr/parse-text", summary="Mask and extract fields from typed text (nothing stored)")
def ocr_parse_text(request: Request, body: Body = Depends(json_body), _: Actor = Depends(staff)):
    text = body.string("Text", required=True, max_length=5000)
    body.raise_if_invalid()
    return ok(_dto(_client(request).post("/v1/ocr/parse-text", {"text": text})))
