"""Built-in, rule-based analytics (ported from the C# AI services).

Deliberately simple and fully explainable statistics, NOT a trained model: a trailing-30-day demand trend,
stock-cover risk, a queue-wait estimate and four anomaly rules over the verification audit log. They are
used directly by the dashboards and as the fallback when the optional Python AI service is unavailable.
Alerts are review prompts — never proof of fraud.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.database.enums import (
    AIAlertSeverity,
    AIAlertStatus,
    AIRiskLevel,
    NotificationType,
    RationType,
    TokenStatus,
    VerificationAction,
)
from app.database.models import (
    AIAlert,
    AIInsight,
    Inventory,
    Notification,
    RationCollection,
    RationCollectionItem,
    RationShop,
    TimeSlot,
    Token,
    User,
    VerificationAuditLog,
)
from app.utils.dotnet import dt, num, one_decimal, qty_text, ymd_hm
from app.utils.time import utc_now

AVERAGE_MINUTES_PER_COLLECTION = 4   # documented stand-in for a measured per-collection counter time


def _round(value: Decimal, places: str) -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_EVEN)   # .NET Math.Round(decimal) default


# ---------------------------------------------------------------- demand, stock, queue

def demand_forecast(db: Session, shop_id: int | None = None) -> list[dict]:
    now = utc_now()
    last30_start, prior30_start = now - timedelta(days=30), now - timedelta(days=60)
    q = (select(RationCollectionItem.RationType, RationCollectionItem.Quantity, RationCollection.CollectedAt)
         .join(RationCollection, RationCollection.Id == RationCollectionItem.RationCollectionId)
         .where(RationCollection.CollectedAt >= prior30_start))
    if shop_id is not None:
        q = q.where(RationCollection.RationShopId == shop_id)
    rows = db.execute(q).all()
    out = []
    for rtype in RationType:
        last30 = sum((qty for t, qty, at in rows if t == rtype and at >= last30_start), start=Decimal(0))
        prior30 = sum((qty for t, qty, at in rows if t == rtype and prior30_start <= at < last30_start), start=Decimal(0))
        growth = float((last30 - prior30) / prior30) * 100.0 if prior30 > 0 else 0.0
        predicted = last30 * (1 + Decimal(str(growth)) / 100)
        out.append({"rationType": rtype.name, "last30DaysKg": num(last30), "previous30DaysKg": num(prior30),
                    "growthPercent": round(growth, 1), "predictedNext30DaysKg": num(_round(max(Decimal(0), predicted), "0.1"))})
    return out


def inventory_risks(db: Session, shop_id: int | None = None) -> list[dict]:
    q = select(Inventory, RationShop.ShopName).join(RationShop, RationShop.Id == Inventory.RationShopId)
    if shop_id is not None:
        q = q.where(Inventory.RationShopId == shop_id)
    stock = db.execute(q.order_by(Inventory.Id)).all()
    since = utc_now() - timedelta(days=14)
    consumption = db.execute(
        select(RationCollection.RationShopId, RationCollectionItem.RationType, RationCollectionItem.Quantity)
        .join(RationCollection, RationCollection.Id == RationCollectionItem.RationCollectionId)
        .where(RationCollection.CollectedAt >= since)).all()
    out = []
    for item, shop_name in stock:
        consumed = sum((q for s, t, q in consumption if s == item.RationShopId and t == item.RationType), start=Decimal(0))
        avg_daily = consumed / 14
        status = ("CRITICAL" if item.AvailableQuantity <= item.MinimumStockLevel * Decimal("0.5")
                  else "LOW" if item.AvailableQuantity <= item.MinimumStockLevel else "NORMAL")
        days = float((item.AvailableQuantity - item.MinimumStockLevel) / avg_daily) if avg_daily > 0 else None
        on_hand = qty_text(item.AvailableQuantity)
        explanation = (f"Consuming ~{one_decimal(avg_daily)} kg/day over the last 14 days; {on_hand} kg on hand." if avg_daily > 0
                       else f"No recent consumption recorded; {on_hand} kg on hand.")
        out.append({"shopId": item.RationShopId, "shopName": shop_name, "rationType": RationType(item.RationType).name,
                    "currentStatus": status, "availableQuantity": num(item.AvailableQuantity),
                    "averageDailyConsumption": num(_round(avg_daily, "0.01")),
                    "predictedDaysUntilReorder": round(days, 1) if days is not None else None, "explanation": explanation})
    return out


def queue_predictions(db: Session, shop_id: int | None = None) -> list[dict]:
    today = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    q = select(RationShop).where(RationShop.IsActive.is_(True))
    if shop_id is not None:
        q = q.where(RationShop.Id == shop_id)
    out = []
    for shop in db.scalars(q.order_by(RationShop.Id)):
        pending = db.scalar(select(func.count()).select_from(Token).join(TimeSlot, TimeSlot.Id == Token.TimeSlotId).where(
            Token.RationShopId == shop.Id, TimeSlot.SlotDate >= today, TimeSlot.SlotDate < today + timedelta(days=1),
            Token.Status.in_([int(TokenStatus.Pending), int(TokenStatus.Confirmed)]))) or 0
        out.append({"shopId": shop.Id, "shopName": shop.ShopName, "pendingInQueue": pending,
                    "predictedWaitMinutes": pending * AVERAGE_MINUTES_PER_COLLECTION,
                    "explanation": f"{pending} beneficiaries pending today × ~{AVERAGE_MINUTES_PER_COLLECTION} min average verification/collection time."})
    return out


# ---------------------------------------------------------------- anomaly rules

def _upsert_alert(db: Session, created: list[AIAlert], alert_type: str, severity: AIAlertSeverity, *,
                  shop_id: int | None = None, beneficiary_id: int | None = None, description: str = "") -> None:
    """Never duplicates an already-open alert for the same subject within the 24-hour window."""
    window = utc_now() - timedelta(hours=24)
    exists = db.scalar(select(AIAlert.Id).where(
        AIAlert.AlertType == alert_type,
        AIAlert.ShopId.is_(None) if shop_id is None else AIAlert.ShopId == shop_id,
        AIAlert.BeneficiaryId.is_(None) if beneficiary_id is None else AIAlert.BeneficiaryId == beneficiary_id,
        AIAlert.Status == int(AIAlertStatus.Open), AIAlert.CreatedAt >= window).limit(1))
    if exists:
        return
    alert = AIAlert(ShopId=shop_id, BeneficiaryId=beneficiary_id, AlertType=alert_type, Severity=int(severity), Description=description,
                    Status=int(AIAlertStatus.Open), CreatedAt=utc_now(), Source="RULES")
    db.add(alert)
    created.append(alert)
    if shop_id is not None:
        owner = db.scalar(select(User.Id).where(User.RationShopId == shop_id).order_by(User.Id).limit(1))
        if owner is not None:
            db.add(Notification(UserId=owner, Type=int(NotificationType.AIAlert), Title=f"AI Alert: {alert_type}",
                                Message=description, IsRead=False, CreatedAt=utc_now()))


def _groups(logs: list[VerificationAuditLog], key) -> dict:
    groups: dict = {}
    for log in logs:
        groups.setdefault(key(log), []).append(log)
    return groups


def scan_and_detect(db: Session) -> list[AIAlert]:
    now = utc_now()
    window = now - timedelta(hours=24)
    recent = list(db.scalars(select(VerificationAuditLog).where(VerificationAuditLog.Timestamp >= window).order_by(VerificationAuditLog.Id)))
    created: list[AIAlert] = []

    # 1. Repeated QR scans for the same beneficiary.
    for ben, logs in _groups([x for x in recent if x.Action == VerificationAction.QrScanned and x.BeneficiaryId is not None],
                             lambda x: x.BeneficiaryId).items():
        if len(logs) > 3:
            _upsert_alert(db, created, "RepeatedQrScan", AIAlertSeverity.Medium, beneficiary_id=ben,
                          description=f"{len(logs)} QR scans for this beneficiary in the last 24 hours.")
    # 2. Duplicate collection attempts on the same token.
    for token_number, logs in _groups([x for x in recent if x.Action == VerificationAction.CollectionRejected and x.TokenNumber is not None],
                                      lambda x: x.TokenNumber).items():
        if len(logs) >= 2:
            _upsert_alert(db, created, "DuplicateCollectionAttempt", AIAlertSeverity.High, shop_id=logs[0].ShopId,
                          beneficiary_id=logs[0].BeneficiaryId,
                          description=f"{len(logs)} rejected collection attempts on token {token_number} in the last 24 hours.")
    # 3. Repeated blocked verification for the same beneficiary.
    for ben, logs in _groups([x for x in recent if x.Action == VerificationAction.BeneficiaryVerified and x.Status == "BLOCKED"
                              and x.BeneficiaryId is not None], lambda x: x.BeneficiaryId).items():
        if len(logs) >= 3:
            _upsert_alert(db, created, "RepeatedFailedVerification", AIAlertSeverity.Medium, beneficiary_id=ben,
                          description=f"{len(logs)} blocked verification attempts for this beneficiary in the last 24 hours.")
    # 4. Unusual shop activity: today's scans vs the trailing 6-day daily average.
    week = db.execute(select(VerificationAuditLog.ShopId, VerificationAuditLog.Timestamp).where(
        VerificationAuditLog.Timestamp >= now - timedelta(days=7), VerificationAuditLog.Action == int(VerificationAction.QrScanned),
        VerificationAuditLog.ShopId.is_not(None))).all()
    by_shop: dict[int, list] = {}
    for shop, at in week:
        by_shop.setdefault(shop, []).append(at)
    for shop, stamps in by_shop.items():
        today_count = sum(1 for at in stamps if at >= window)
        daily_average = sum(1 for at in stamps if at < window) / 6.0
        if daily_average > 0 and today_count > daily_average * 2:
            _upsert_alert(db, created, "UnusualShopActivity", AIAlertSeverity.Low, shop_id=shop,
                          description=f"{today_count} QR scans today vs a {one_decimal(daily_average)}/day trailing average.")
    if created:
        db.commit()
    return created


def recent_alerts(db: Session, take: int = 20) -> list[AIAlert]:
    return list(db.scalars(select(AIAlert).order_by(AIAlert.CreatedAt.desc(), AIAlert.Id.desc()).limit(take)))


def alert_entity(a: AIAlert) -> dict:
    """GET /api/ai/alerts returned the raw C# entity: every column, enums as numbers."""
    return {"id": a.Id, "shopId": a.ShopId, "beneficiaryId": a.BeneficiaryId, "alertType": a.AlertType, "severity": a.Severity,
            "description": a.Description, "status": a.Status, "createdAt": dt(a.CreatedAt), "resolvedAt": dt(a.ResolvedAt),
            "source": a.Source, "title": a.Title, "rationType": a.RationType, "score": a.Score, "recommendedAction": a.RecommendedAction,
            "dedupKey": a.DedupKey, "metadataJson": a.MetadataJson, "detectedAt": dt(a.DetectedAt), "lastSeenAt": dt(a.LastSeenAt),
            "resolvedByUserId": a.ResolvedByUserId, "resolutionNote": a.ResolutionNote}


# ---------------------------------------------------------------- insights

def _record_insight(db: Session, entity_type: str, entity_id: int, insight_type: str, risk: AIRiskLevel, score: float,
                    explanation: str, recommendation: str) -> None:
    db.add(AIInsight(EntityType=entity_type, EntityId=entity_id, InsightType=insight_type, RiskLevel=int(risk), Score=score,
                     Explanation=explanation, Recommendation=recommendation, CreatedAt=utc_now()))
    db.commit()


def beneficiary_insight(db: Session, beneficiary_id: int) -> dict:
    window = utc_now() - timedelta(hours=24)
    logs = db.scalars(select(VerificationAuditLog).where(VerificationAuditLog.BeneficiaryId == beneficiary_id,
                                                         VerificationAuditLog.Timestamp >= window)).all()
    scans = sum(1 for x in logs if x.Action == VerificationAction.QrScanned)
    blocked = sum(1 for x in logs if x.Action == VerificationAction.BeneficiaryVerified and x.Status == "BLOCKED")
    open_alerts = db.scalar(select(func.count()).select_from(AIAlert).where(
        AIAlert.BeneficiaryId == beneficiary_id, AIAlert.Status == int(AIAlertStatus.Open))) or 0
    reasons = []
    if scans > 3:
        reasons.append(f"{scans} repeated QR scan attempts in the last 24 hours")
    if blocked > 0:
        reasons.append(f"{blocked} blocked verification attempt(s) recently")
    if open_alerts > 0:
        reasons.append(f"{open_alerts} open anomaly alert(s) on record")
    if open_alerts >= 2 or blocked >= 3:
        level, risk = "High", AIRiskLevel.High
        explanation = "Multiple unresolved anomaly signals for this beneficiary — review verification history before confirming collection."
    elif reasons:
        level, risk = "Medium", AIRiskLevel.Medium
        explanation = "Some recent activity is outside the beneficiary's usual pattern — a quick review is recommended."
    else:
        level, risk = "Low", AIRiskLevel.Low
        explanation = "Collection pattern is consistent with the beneficiary's entitlement schedule."
        reasons.append("No anomalies detected in the last 24 hours")
    _record_insight(db, "Beneficiary", beneficiary_id, "BeneficiaryRisk", risk, scans + blocked + open_alerts, explanation,
                    "No action required." if level == "Low" else "Review verification history before confirming collection.")
    return {"riskLevel": level, "reasons": reasons, "explanation": explanation}


def shop_insight(db: Session, shop_id: int) -> dict:
    shop = db.get(RationShop, shop_id)
    if shop is None:
        raise NotFound("Ration shop not found.")
    risks = inventory_risks(db, shop_id)
    inventory = ("CRITICAL" if any(r["currentStatus"] == "CRITICAL" for r in risks)
                 else "LOW" if any(r["currentStatus"] == "LOW" for r in risks) else "NORMAL")
    demand = demand_forecast(db, shop_id)
    growth = mean(d["growthPercent"] for d in demand) if demand else 0.0
    demand_level = "HIGH" if growth > 15 else "MODERATE" if growth > 0 else "STABLE"
    queue = queue_predictions(db, shop_id)
    wait = queue[0]["predictedWaitMinutes"] if queue else 0
    queue_health = "HIGH" if wait > 60 else "MODERATE" if wait > 20 else "LOW"
    alerts = db.scalar(select(func.count()).select_from(AIAlert).where(AIAlert.ShopId == shop_id, AIAlert.Status == int(AIAlertStatus.Open))) or 0
    anomaly = "HIGH" if alerts >= 3 else "MEDIUM" if alerts >= 1 else "LOW"
    if inventory == "CRITICAL":
        trend = f" (+{one_decimal(growth)}% trend)" if growth > 0 else ""
        recommendation = f"Increase stock before predicted demand{trend} — inventory is critical."
    elif demand_level == "HIGH":
        recommendation = "Demand is trending up — consider a stock top-up ahead of the predicted peak."
    elif queue_health == "HIGH":
        recommendation = "Queue wait times are high — consider adding an additional counter slot."
    elif anomaly != "LOW":
        recommendation = "Review recent anomaly alerts for this shop."
    else:
        recommendation = "No immediate action required."
    risk = (AIRiskLevel.High if anomaly == "HIGH" or inventory == "CRITICAL"
            else AIRiskLevel.Medium if anomaly == "MEDIUM" or inventory == "LOW" or queue_health == "HIGH" else AIRiskLevel.Low)
    _record_insight(db, "Shop", shop.Id, "ShopRisk", risk, growth,
                    f"Inventory {inventory}, demand {demand_level}, queue {queue_health}, anomalies {anomaly}.", recommendation)
    return {"shopId": shop.Id, "shopName": shop.ShopName, "inventoryHealth": inventory, "demandLevel": demand_level,
            "queueHealth": queue_health, "anomalyLevel": anomaly, "recommendation": recommendation}


def intelligence_center(db: Session) -> dict:
    scan_and_detect(db)
    demand, risks, queue, alerts = demand_forecast(db), inventory_risks(db), queue_predictions(db), recent_alerts(db)
    return {
        "demandForecast": demand, "inventoryRisks": risks, "queuePredictions": queue,
        "recentAnomalies": [{"id": a.Id, "shopId": a.ShopId, "beneficiaryId": a.BeneficiaryId, "alertType": a.AlertType,
                             "severity": AIAlertSeverity(a.Severity).name, "description": a.Description,
                             "status": AIAlertStatus(a.Status).name, "createdAt": ymd_hm(a.CreatedAt)} for a in alerts],
        "shopsRequiringAttention": len({r["shopId"] for r in risks if r["currentStatus"] != "NORMAL"}),
        "averageQueueWaitMinutes": round(mean(q["predictedWaitMinutes"] for q in queue), 1) if queue else 0,
        "anomaliesRequiringReview": sum(1 for a in alerts if a.Status == AIAlertStatus.Open),
        "isSyntheticData": True,
    }
