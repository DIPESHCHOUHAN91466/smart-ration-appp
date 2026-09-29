"""Government / admin views: today's dashboard, statistics and reports for a date range, the shop map
(markers, one shop's detail, heatmap analytics) and the read-only database viewer.

DEMO MAP DATA: shop coordinates are the synthetic demo coordinates; heatmap weights are counts from the
database, never individual beneficiary locations (which this system does not collect).
Nothing in this module writes to the database.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.database.enums import (
    AadhaarVerificationStatus,
    AIRiskLevel,
    EligibilityStatus,
    FamilyRelationship,
    Gender,
    PassbookVerificationStatus,
    RationType,
    TokenStatus,
    UserRole,
    parse_enum,
)
from app.database.models import (
    AadhaarVerification,
    AIInsight,
    AuditLog,
    Beneficiary,
    Family,
    FamilyMember,
    Inventory,
    PassbookVerification,
    RationCollection,
    RationCollectionItem,
    RationScheme,
    RationShop,
    TimeSlot,
    Token,
    TokenItem,
    User,
    VerificationAuditLog,
)
from app.services import verification_audit_service
from app.services.mappers import inventory_dto
from app.utils.dotnet import dt, enum_name, num, ymd, ymd_hm
from app.utils.time import utc_now

PENDING = (int(TokenStatus.Pending), int(TokenStatus.Confirmed))


def _today() -> datetime:
    return utc_now().replace(hour=0, minute=0, second=0, microsecond=0)


def _day_range(q: Select, column, start: datetime, end_inclusive: datetime) -> Select:
    return q.where(column >= start, column < end_inclusive + timedelta(days=1))


# ---------------------------------------------------------------- dashboard, statistics, reports

def dashboard(db: Session) -> dict:
    today = _today()
    statuses = db.scalars(_day_range(select(Token.Status).join(TimeSlot, TimeSlot.Id == Token.TimeSlotId), TimeSlot.SlotDate, today, today)).all()
    distributed = db.scalars(_day_range(select(TokenItem.Quantity).join(Token, Token.Id == TokenItem.TokenId)
                                        .where(Token.Status == int(TokenStatus.Completed)), Token.CollectedAt, today, today)).all()
    return {
        "totalBeneficiaries": db.scalar(select(func.count()).select_from(User).where(User.Role == int(UserRole.RuralUser), User.IsActive.is_(True))) or 0,
        "totalShops": db.scalar(select(func.count()).select_from(RationShop).where(RationShop.IsActive.is_(True))) or 0,
        "todayBookings": len(statuses),
        "todayCollections": sum(1 for s in statuses if s == TokenStatus.Completed),
        "pendingCollections": sum(1 for s in statuses if s in PENDING),
        "rationDistributedTodayKg": num(sum(distributed, start=Decimal(0))),
        "lowStockAlerts": db.scalar(select(func.count()).select_from(Inventory).where(Inventory.AvailableQuantity <= Inventory.MinimumStockLevel)) or 0,
    }


def normalize_range(from_date: datetime | None, to_date: datetime | None) -> tuple[datetime, datetime]:
    to = (to_date or utc_now()).replace(hour=0, minute=0, second=0, microsecond=0)
    start = (from_date or to - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (start, to) if start <= to else (to, start)


def _percent(part: int, whole: int) -> float:
    return 0 if whole == 0 else round(part * 100.0 / whole, 1)


def statistics(db: Session, from_date: datetime | None, to_date: datetime | None) -> dict:
    start, end = normalize_range(from_date, to_date)
    rows = db.execute(_day_range(select(Token.RationShopId, Token.Status, RationShop.ShopName)
                                 .join(RationShop, RationShop.Id == Token.RationShopId), Token.CreatedAt, start, end).order_by(Token.Id)).all()
    completed = sum(1 for _, s, _ in rows if s == TokenStatus.Completed)
    shops: dict[int, dict] = {}
    for shop_id, status, name in rows:
        entry = shops.setdefault(shop_id, {"shopId": shop_id, "shopName": name, "totalTokens": 0, "completedTokens": 0})
        entry["totalTokens"] += 1
        entry["completedTokens"] += status == TokenStatus.Completed
    performance = [{**e, "efficiencyPercent": _percent(e["completedTokens"], e["totalTokens"])} for e in shops.values()]
    performance.sort(key=lambda e: e["efficiencyPercent"], reverse=True)   # stable, like LINQ OrderByDescending
    return {"fromDate": dt(start), "toDate": dt(end), "tokensGenerated": len(rows), "collectionsCompleted": completed,
            "collectionsCancelled": sum(1 for _, s, _ in rows if s == TokenStatus.Cancelled),
            "collectionEfficiencyPercent": _percent(completed, len(rows)), "shopPerformance": performance}


def reports(db: Session, from_date: datetime | None, to_date: datetime | None) -> list[dict]:
    start, end = normalize_range(from_date, to_date)
    statuses = db.scalars(_day_range(select(Token.Status), Token.CreatedAt, start, end)).all()
    verifications = db.scalar(_day_range(select(func.count()).select_from(AuditLog).where(AuditLog.Action == "COLLECTION_COMPLETED"),
                                         AuditLog.CreatedAt, start, end)) or 0

    def report(name: str, description: str, count: int) -> dict:
        return {"reportName": name, "description": description, "recordCount": count, "exportAvailable": False}

    return [
        report("Daily Collection Report", "Ration collections completed in range", sum(1 for s in statuses if s == TokenStatus.Completed)),
        report("Token Generation Report", "Ration tokens generated in range", len(statuses)),
        report("QR Verification Report", "Successful QR verifications resulting in collection", verifications),
        report("Cancelled Bookings Report", "Bookings cancelled in range", sum(1 for s in statuses if s == TokenStatus.Cancelled)),
    ]


# ---------------------------------------------------------------- map

def _shop_stats(db: Session, shop_id: int) -> dict:
    today = _today()
    statuses = db.scalars(_day_range(select(Token.Status).join(TimeSlot, TimeSlot.Id == Token.TimeSlotId)
                                     .where(Token.RationShopId == shop_id), TimeSlot.SlotDate, today, today)).all()
    in_shop = select(Beneficiary.Id).join(Family, Family.Id == Beneficiary.FamilyId).where(Family.RationShopId == shop_id)
    eligible = db.scalar(select(func.count()).select_from(in_shop.where(Beneficiary.IsActive.is_(True), Beneficiary.IsBlocked.is_(False)).subquery())) or 0
    issues = db.scalar(select(func.count()).select_from(AadhaarVerification).where(
        AadhaarVerification.BeneficiaryId.in_(in_shop), AadhaarVerification.Status != int(AadhaarVerificationStatus.Verified))) or 0
    return {"todayBookings": len(statuses), "completedCollections": sum(1 for s in statuses if s == TokenStatus.Completed),
            "pendingCollections": sum(1 for s in statuses if s in PENDING), "eligibleBeneficiaries": eligible, "verificationIssues": issues}


def _inventory_status(db: Session, shop_id: int) -> tuple[str, Decimal]:
    stock = db.scalars(select(Inventory).where(Inventory.RationShopId == shop_id)).all()
    if not stock:
        return "Normal", Decimal(0)
    worst = max(i.MinimumStockLevel - i.AvailableQuantity for i in stock)
    status = ("Critical" if any(i.AvailableQuantity <= i.MinimumStockLevel * Decimal("0.5") for i in stock)
              else "Low" if any(i.AvailableQuantity <= i.MinimumStockLevel for i in stock) else "Normal")
    return status, max(Decimal(0), worst)


def map_markers(db: Session, state: str | None, district: str | None, taluka: str | None, village: str | None,
                scheme_code: str | None, inventory_status: str | None) -> list[dict]:
    q = select(RationShop).where(RationShop.IsActive.is_(True))
    for column, value in ((RationShop.State, state), (RationShop.District, district), (RationShop.Taluka, taluka), (RationShop.Village, village)):
        if value and value.strip():
            q = q.where(column == value)
    if scheme_code and scheme_code.strip():
        q = q.where(RationShop.Id.in_(select(Family.RationShopId).join(RationScheme, RationScheme.Id == Family.RationSchemeId)
                                      .where(RationScheme.SchemeCode == scheme_code)))
    markers = []
    for shop in db.scalars(q.order_by(RationShop.Id)):
        status, _ = _inventory_status(db, shop.Id)
        markers.append({"id": shop.Id, "shopName": shop.ShopName, "shopCode": shop.ShopCode, "latitude": shop.Latitude,
                        "longitude": shop.Longitude, "state": shop.State, "district": shop.District, "taluka": shop.Taluka,
                        "village": shop.Village, "inventoryStatus": status, **_shop_stats(db, shop.Id), "dataSource": "SYNTHETIC_DEMO"})
    if inventory_status and inventory_status.strip():
        markers = [m for m in markers if m["inventoryStatus"].lower() == inventory_status.lower()]
    return markers


def shop_detail(db: Session, shop_id: int) -> dict:
    shop = db.get(RationShop, shop_id)
    if shop is None:
        raise NotFound("Ration shop not found.")
    operator = db.scalar(select(User.FullName).where(User.RationShopId == shop_id, User.Role == int(UserRole.ShopOwner)).order_by(User.Id).limit(1))
    stock = db.scalars(select(Inventory).where(Inventory.RationShopId == shop_id).order_by(Inventory.Id)).all()
    return {"id": shop.Id, "shopName": shop.ShopName, "shopCode": shop.ShopCode, "operatorName": operator,
            "village": shop.Village if shop.Village is not None else shop.Address, "district": shop.District, "state": shop.State,
            "latitude": shop.Latitude, "longitude": shop.Longitude, "inventory": [inventory_dto(i) for i in stock], **_shop_stats(db, shop_id)}


def map_analytics(db: Session) -> dict:
    shops = db.scalars(select(RationShop).order_by(RationShop.Id)).all()
    density, demand, activity, shortage = [], [], [], []
    low = critical = today_collections = pending = 0
    for shop in shops:
        stats = _shop_stats(db, shop.Id)
        status, shortfall = _inventory_status(db, shop.Id)
        low += status == "Low"
        critical += status == "Critical"
        today_collections += stats["completedCollections"]
        pending += stats["pendingCollections"]

        def point(intensity, shop=shop):
            return {"lat": shop.Latitude, "lng": shop.Longitude, "intensity": num(intensity)}

        if stats["eligibleBeneficiaries"] > 0:
            density.append(point(stats["eligibleBeneficiaries"]))
        if stats["todayBookings"] > 0:
            demand.append(point(stats["todayBookings"]))
        if stats["completedCollections"] > 0:
            activity.append(point(stats["completedCollections"]))
        if shortfall > 0:
            shortage.append(point(shortfall))
    return {
        "totalShops": len(shops), "activeShops": sum(1 for s in shops if s.IsActive), "lowInventoryShops": low,
        "criticalInventoryShops": critical,
        "totalBeneficiaries": db.scalar(select(func.count()).select_from(Beneficiary)
                                        .where(Beneficiary.IsActive.is_(True), Beneficiary.IsBlocked.is_(False))) or 0,
        "eligibleBeneficiaries": db.scalar(select(func.count()).select_from(FamilyMember)
                                           .where(FamilyMember.Eligibility == int(EligibilityStatus.Eligible))) or 0,
        "todayCollections": today_collections, "pendingCollections": pending,
        "beneficiaryDensityHeatmap": density, "demandHeatmap": demand, "collectionActivityHeatmap": activity,
        "inventoryShortageHeatmap": shortage, "isSyntheticData": True,
    }


# ---------------------------------------------------------------- read-only database viewer

TABLES = ["beneficiaries", "familyMembers", "tokens", "collections", "inventory", "aiInsights", "auditLogs"]


def _like(term: str):
    text = term.strip().lower().replace("!", "!!").replace("%", "!%").replace("_", "!_")
    pattern = f"%{text}%"
    return lambda column: func.lower(column).like(pattern, escape="!")


def _page(db: Session, q: Select, page: int, size: int) -> tuple[int, list]:
    total = db.scalar(select(func.count()).select_from(q.order_by(None).subquery())) or 0
    return total, list(db.execute(q.offset((page - 1) * size).limit(size)).all())


def _paged(items: list[dict], total: int, page: int, size: int) -> dict:
    return {"items": items, "totalCount": total, "page": page, "pageSize": size}


def beneficiaries_page(db: Session, search: str | None, page: int, size: int, *, district: str | None = None,
                       aadhaar_status: str | None = None, passbook_status: str | None = None, search_mobile: bool = False) -> dict:
    q = (select(Beneficiary, User.FullName, RationScheme.SchemeCode, RationShop.ShopName, AadhaarVerification.Status,
                PassbookVerification.VerificationStatus)
         .join(User, User.Id == Beneficiary.UserId).join(Family, Family.Id == Beneficiary.FamilyId)
         .join(RationScheme, RationScheme.Id == Family.RationSchemeId).join(RationShop, RationShop.Id == Family.RationShopId)
         .outerjoin(AadhaarVerification, AadhaarVerification.BeneficiaryId == Beneficiary.Id)
         .outerjoin(PassbookVerification, PassbookVerification.BeneficiaryId == Beneficiary.Id))
    if search and search.strip():
        like = _like(search)
        conditions = [like(Beneficiary.BeneficiaryCode), like(User.FullName)]
        if search_mobile:
            conditions.append(like(User.MobileNumber))
        q = q.where(or_(*conditions))
    if district and district.strip():
        q = q.where(Beneficiary.District == district)
    aadhaar = parse_enum(AadhaarVerificationStatus, aadhaar_status) if aadhaar_status else None   # unknown names are ignored
    if aadhaar is not None:
        q = q.where(AadhaarVerification.Status == int(aadhaar))
    passbook = parse_enum(PassbookVerificationStatus, passbook_status) if passbook_status else None
    if passbook is not None:
        q = q.where(PassbookVerification.VerificationStatus == int(passbook))
    total, rows = _page(db, q.order_by(Beneficiary.Id), page, size)
    family_ids = {r[0].FamilyId for r in rows}
    sizes = dict(db.execute(select(FamilyMember.FamilyId, func.count()).where(FamilyMember.FamilyId.in_(family_ids))
                            .group_by(FamilyMember.FamilyId)).tuples().all()) if family_ids else {}
    items = [{"id": b.Id, "beneficiaryCode": b.BeneficiaryCode, "fullName": name, "gender": enum_name(Gender, b.Gender),
              "village": b.Village, "district": b.District, "state": b.State, "schemeCode": scheme, "shopName": shop,
              "familySize": sizes.get(b.FamilyId, 0),
              "aadhaarStatus": enum_name(AadhaarVerificationStatus, a) if a is not None else "NotVerified",
              "passbookStatus": enum_name(PassbookVerificationStatus, p) if p is not None else "NotVerified",
              "isActive": bool(b.IsActive), "isBlocked": bool(b.IsBlocked)} for b, name, scheme, shop, a, p in rows]
    return _paged(items, total, page, size)


def family_members_page(db: Session, search: str | None, page: int, size: int) -> dict:
    q = select(FamilyMember, Family.FamilyCode).join(Family, Family.Id == FamilyMember.FamilyId)
    if search and search.strip():
        like = _like(search)
        q = q.where(or_(like(FamilyMember.FullName), like(Family.FamilyCode)))
    total, rows = _page(db, q.order_by(FamilyMember.Id), page, size)
    return _paged([{"id": m.Id, "familyCode": code, "fullName": m.FullName, "age": m.Age,
                    "relationship": enum_name(FamilyRelationship, m.Relationship), "eligibility": enum_name(EligibilityStatus, m.Eligibility)}
                   for m, code in rows], total, page, size)


def tokens_page(db: Session, search: str | None, page: int, size: int) -> dict:
    code = select(Beneficiary.BeneficiaryCode).where(Beneficiary.UserId == Token.UserId).order_by(Beneficiary.Id).limit(1).scalar_subquery()
    q = (select(Token, code, RationShop.ShopName, TimeSlot.SlotDate).join(RationShop, RationShop.Id == Token.RationShopId)
         .join(TimeSlot, TimeSlot.Id == Token.TimeSlotId))
    if search and search.strip():
        q = q.where(_like(search)(Token.TokenNumber))
    total, rows = _page(db, q.order_by(Token.Id.desc()), page, size)
    return _paged([{"id": t.Id, "tokenNumber": t.TokenNumber, "beneficiaryCode": ben or "—", "shopName": shop, "slotDate": ymd(day),
                    "status": enum_name(TokenStatus, t.Status), "qrCodeValue": t.QRCodeValue} for t, ben, shop, day in rows], total, page, size)


def collections_page(db: Session, search: str | None, page: int, size: int) -> dict:
    q = (select(RationCollection, Beneficiary.BeneficiaryCode, RationShop.ShopName)
         .join(Beneficiary, Beneficiary.Id == RationCollection.BeneficiaryId).join(RationShop, RationShop.Id == RationCollection.RationShopId))
    if search and search.strip():
        q = q.where(_like(search)(RationCollection.CollectionCode))
    total, rows = _page(db, q.order_by(RationCollection.CollectedAt.desc(), RationCollection.Id.desc()), page, size)
    ids = [r[0].Id for r in rows]
    totals: dict[int, Decimal] = {}
    for cid, qty in db.execute(select(RationCollectionItem.RationCollectionId, RationCollectionItem.Quantity)
                               .where(RationCollectionItem.RationCollectionId.in_(ids))) if ids else []:
        totals[cid] = totals.get(cid, Decimal(0)) + qty
    return _paged([{"id": c.Id, "collectionCode": c.CollectionCode, "beneficiaryCode": ben, "shopName": shop,
                    "collectedAt": ymd_hm(c.CollectedAt), "totalQuantityKg": num(totals.get(c.Id, Decimal(0)))}
                   for c, ben, shop in rows], total, page, size)


def inventory_page(db: Session, page: int, size: int) -> dict:
    q = select(Inventory, RationShop.ShopName).join(RationShop, RationShop.Id == Inventory.RationShopId)
    total, rows = _page(db, q.order_by(Inventory.RationShopId, Inventory.Id), page, size)
    return _paged([{"id": i.Id, "shopName": shop, "rationType": enum_name(RationType, i.RationType), "available": num(i.AvailableQuantity),
                    "allocated": num(i.AllocatedQuantity), "minimumStockLevel": num(i.MinimumStockLevel)} for i, shop in rows], total, page, size)


def insights_page(db: Session, page: int, size: int) -> dict:
    total, rows = _page(db, select(AIInsight).order_by(AIInsight.CreatedAt.desc(), AIInsight.Id.desc()), page, size)
    return _paged([{"id": i.Id, "entityType": i.EntityType, "entityId": i.EntityId, "insightType": i.InsightType,
                    "riskLevel": enum_name(AIRiskLevel, i.RiskLevel), "score": i.Score, "explanation": i.Explanation,
                    "createdAt": ymd_hm(i.CreatedAt)} for (i,) in rows], total, page, size)


def audit_logs_page(db: Session, page: int, size: int) -> dict:
    total, rows = _page(db, select(VerificationAuditLog).order_by(VerificationAuditLog.Timestamp.desc(), VerificationAuditLog.Id.desc()), page, size)
    return _paged([verification_audit_service.to_dto(x) for (x,) in rows], total, page, size)
