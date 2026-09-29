"""Government / admin: dashboard, statistics, reports, users, the shop map and the read-only database viewer.

Migrated from the C# AdminController, GovernmentMapController, ShopsController (map / location),
AdminDatabaseController and SyntheticDataController. Officials and admins only; nothing here writes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import OFFICIALS, Actor, actor
from app.api.routes._common import parse_date
from app.core.errors import fail_body, ok
from app.database.connection import get_db
from app.services import government_service, profile_service

router = APIRouter(prefix="/api", tags=["government"])
officials = actor(*OFFICIALS)


@router.get("/admin/dashboard", summary="Today's totals across all shops")
def dashboard(_: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(government_service.dashboard(db))


@router.get("/admin/statistics", summary="Tokens, collections and shop efficiency for a date range (default: last 30 days)")
def statistics(fromDate: str | None = None, toDate: str | None = None, _: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(government_service.statistics(db, parse_date("fromDate", fromDate, required=False), parse_date("toDate", toDate, required=False)))


@router.get("/admin/reports", summary="Report record counts for a date range")
def reports(fromDate: str | None = None, toDate: str | None = None, _: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(government_service.reports(db, parse_date("fromDate", fromDate, required=False), parse_date("toDate", toDate, required=False)))


@router.get("/admin/users", summary="User accounts (optionally one role)")
def users(role: str | None = None, _: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(profile_service.list_users(db, role))


# ---------------------------------------------------------------- map

@router.get("/shops/map", summary="Shop markers with today's activity and stock status")
def shop_markers(state: str | None = None, district: str | None = None, taluka: str | None = None, village: str | None = None,
                 schemeCode: str | None = None, inventoryStatus: str | None = None, _: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(government_service.map_markers(db, state, district, taluka, village, schemeCode, inventoryStatus))


@router.get("/shops/{shop_id}/location", summary="One shop's map detail")
def shop_location(shop_id: int, _: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(government_service.shop_detail(db, shop_id))


@router.get("/government/map/analytics", summary="Map totals and heatmap layers (synthetic demo data)")
def map_analytics(_: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(government_service.map_analytics(db))


# ---------------------------------------------------------------- read-only database viewer

@router.get("/admin/database/tables", summary="Tables the viewer can show")
def tables(_: Actor = Depends(officials)):
    return ok(government_service.TABLES)


@router.get("/admin/database/{table}", summary="One page of a table (read-only)")
def table(table: str, search: str | None = None, page: int = 1, pageSize: int = 25, _: Actor = Depends(officials), db: Session = Depends(get_db)):
    page, size = max(1, page), min(max(pageSize, 1), 100)
    views = {
        "beneficiaries": lambda: government_service.beneficiaries_page(db, search, page, size),
        "familymembers": lambda: government_service.family_members_page(db, search, page, size),
        "tokens": lambda: government_service.tokens_page(db, search, page, size),
        "collections": lambda: government_service.collections_page(db, search, page, size),
        "inventory": lambda: government_service.inventory_page(db, page, size),
        "aiinsights": lambda: government_service.insights_page(db, page, size),
        "auditlogs": lambda: government_service.audit_logs_page(db, page, size),
    }
    view = views.get(table.lower())
    if view is None:
        return JSONResponse(status_code=404, content=fail_body(f"Unknown table '{table}'. Supported: {', '.join(government_service.TABLES)}"))
    return ok(view())


@router.get("/admin/synthetic-data/beneficiaries", summary="Synthetic beneficiary dataset (search / filter / pages)")
def synthetic_beneficiaries(search: str | None = None, district: str | None = None, aadhaarStatus: str | None = None,
                            passbookStatus: str | None = None, page: int = 1, pageSize: int = 20,
                            _: Actor = Depends(officials), db: Session = Depends(get_db)):
    return ok(government_service.beneficiaries_page(db, search, max(1, page), min(max(pageSize, 1), 100), district=district,
                                                    aadhaar_status=aadhaarStatus, passbook_status=passbookStatus, search_mobile=True))
