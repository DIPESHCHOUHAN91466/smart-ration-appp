"""Migrated account / beneficiary / search / AI / government routes (formerly served by the C# API).

Runs on the shared synthetic ration world (tests/ration_world.py). The optional AI service is faked with
httpx.MockTransport; with no AI service the analytics answer from the built-in rules ("fallback").
"""

from __future__ import annotations

import json

import httpx
import pytest
from ration_world import TEST_PASSWORD, book, qr_payload, session
from sqlalchemy import select

from app.database.enums import AIAlertStatus
from app.database.models import AIAlert, AIInsight, AuditLog, Beneficiary


def register(env, n: int) -> dict:
    r = env["client"].post("/api/auth/register", json={"fullName": f"Citizen {n}", "email": f"c{n}@example.com",
                                                       "mobileNumber": f"90000001{n:02d}", "password": TEST_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['data']['accessToken']}"}


def my_beneficiary_id(env, headers=None) -> int:
    return env["client"].get("/api/beneficiaries/me", headers=headers or env["citizen"]).json()["data"]["beneficiary"]["id"]


def collect(env) -> dict:
    token = book(env).json()["data"]
    r = env["client"].post("/api/ration/collection/confirm", headers=env["shop"], json={"tokenId": token["id"]})
    assert r.status_code == 200, r.text
    return token


# ---------------------------------------------------------------- own account

def test_profile_read_and_update(env):
    c = env["client"]
    assert c.get("/api/users/profile", headers=env["citizen"]).json()["data"]["email"] == "asha@example.com"
    r = c.put("/api/users/profile", headers=env["citizen"], json={"fullName": "  Asha P  ", "mobileNumber": " 9000000009 "})
    assert r.status_code == 200 and r.json()["data"]["fullName"] == "Asha P" and r.json()["data"]["mobileNumber"] == "9000000009"
    r = c.put("/api/users/profile", headers=env["citizen"], json={"fullName": "Asha", "mobileNumber": "9000000051"})
    assert r.status_code == 409   # the shop owner's number
    r = c.put("/api/users/profile", headers=env["citizen"], json={"fullName": "A", "mobileNumber": "9000000009"})
    assert r.status_code == 400 and r.json()["errors"][0].startswith("FullName:")


# ---------------------------------------------------------------- beneficiary records and access

def test_citizen_sees_only_their_own_beneficiary(env):
    mine = my_beneficiary_id(env)
    other = my_beneficiary_id(env, register(env, 2))
    c = env["client"]
    for path in ("verification", "family", "entitlement", "collections", "full-profile"):
        assert c.get(f"/api/beneficiaries/{mine}/{path}", headers=env["citizen"]).status_code == 200, path
        assert c.get(f"/api/beneficiaries/{other}/{path}", headers=env["citizen"]).status_code == 403, path
        assert c.get(f"/api/beneficiaries/{other}/{path}", headers=env["shop"]).status_code == 200, path
    assert c.get("/api/beneficiaries/9999/verification", headers=env["official"]).status_code == 404
    assert c.get("/api/beneficiaries/me", headers=env["shop"]).status_code == 403


def test_verification_profile_masks_identity(env):
    data = env["client"].get("/api/beneficiaries/me", headers=env["citizen"]).json()["data"]
    assert data["aadhaarVerification"]["aadhaarMasked"].startswith("XXXX-XXXX-")
    assert data["beneficiary"]["mobileMasked"] == "******0001"
    assert "9000000001" not in json.dumps(data)


def test_my_profile_names_my_assigned_shop(env):
    data = env["client"].get("/api/beneficiaries/me", headers=env["citizen"]).json()["data"]
    assert data["rationShop"] == {"id": 1, "shopName": "Satnavari FPS", "shopCode": "FPS-001", "address": "a", "district": "Nagpur"}
    # The staff view of a beneficiary is unchanged.
    staff = env["client"].get(f"/api/beneficiaries/{data['beneficiary']['id']}/verification", headers=env["shop"]).json()["data"]
    assert "rationShop" not in staff


def test_full_profile_after_booking_and_collection(env):
    token = collect(env)
    book(env, slot_id=2)   # an upcoming booking tomorrow
    ben = my_beneficiary_id(env)
    data = env["client"].get(f"/api/beneficiaries/{ben}/full-profile", headers=env["citizen"]).json()["data"]
    assert data["profile"]["lastCollectionDate"] and data["profile"]["nextCollectionDate"]
    assert data["currentQr"]["tokenNumber"] != token["tokenNumber"] and data["currentQr"]["bookingTime"] == "09:00"
    assert data["rationCard"]["schemeCode"] == "DEMO-NFSA" and data["rationCard"]["familySize"] == 1
    assert data["collectionHistory"][0]["items"] == [{"rationType": "Rice", "quantity": 5}, {"rationType": "Wheat", "quantity": 3}]
    assert data["entitlement"]["items"][0]["alreadyCollected"] == 5
    # A citizen never sees fraud-risk signals or the shop's verification/scan logs about them...
    assert data["aiInsight"] is None and data["verificationHistory"] == [] and data["qrScanHistory"] == []
    # ...while staff still do.
    staff = env["client"].get(f"/api/beneficiaries/{ben}/full-profile", headers=env["shop"]).json()["data"]
    assert staff["aiInsight"]["riskLevel"] == "Low"
    assert staff["verificationHistory"] and all(v["action"] for v in staff["verificationHistory"])
    hist = env["client"].get(f"/api/ration/collection/history/{ben}", headers=env["citizen"]).json()["data"]
    assert len(hist) == 1


def test_family_access(env):
    with session() as db:
        family_id = db.scalar(select(Beneficiary.FamilyId))
    c = env["client"]
    assert c.get(f"/api/families/{family_id}", headers=env["citizen"]).json()["data"]["familySize"] == 1
    assert c.get(f"/api/families/{family_id}/entitlement", headers=env["citizen"]).json()["data"]["schemeCode"] == "DEMO-NFSA"
    assert c.get(f"/api/families/{family_id}", headers=register(env, 3)).status_code == 403
    assert c.get("/api/families/9999", headers=env["official"]).status_code == 404


# ---------------------------------------------------------------- search and the public badge

def test_search_is_scoped_by_role(env):
    token = book(env).json()["data"]
    c = env["client"]
    number = token["tokenNumber"]
    mine = c.get("/api/search", params={"q": number}, headers=env["citizen"]).json()["data"]
    assert [r["path"] for r in mine] == [f"/rural/token/{token['id']}"]
    assert c.get("/api/search", params={"q": number}, headers=env["other_shop"]).json()["data"] == []
    assert c.get("/api/search", params={"q": "asha"}, headers=env["shop"]).json()["data"][0]["type"] == "Beneficiary"
    shops = [r for r in c.get("/api/search", params={"q": "fps"}, headers=env["official"]).json()["data"] if r["type"] == "Shop"]
    assert len(shops) == 2
    assert c.get("/api/search", params={"q": "%%"}, headers=env["official"]).json()["data"] == []   # not a wildcard
    assert c.get("/api/search", params={"q": "a"}, headers=env["official"]).json()["data"] == []    # too short


def test_public_badge_has_no_personal_data(env):
    collect(env)
    with session() as db:
        code = db.scalar(select(Beneficiary.BeneficiaryCode))
    r = env["client"].get(f"/api/public/beneficiaries/{code}")   # no login
    assert r.status_code == 200
    badge = r.json()["data"]
    assert set(badge) == {"beneficiaryCode", "schemeCode", "eligibilityBadge", "verificationBadge", "lastCollectionMonth", "shopCode", "region"}
    assert badge["eligibilityBadge"] == "Eligible" and badge["verificationBadge"] == "Verified"
    assert badge["region"] == ", " and badge["shopCode"] == "FPS-001"   # district/state only (blank for self-registered citizens)
    assert badge["lastCollectionMonth"]
    assert env["client"].get("/api/public/beneficiaries/NOPE").status_code == 404


# ---------------------------------------------------------------- built-in AI rules

def test_rule_based_analytics(env):
    collect(env)
    c = env["client"]
    forecast = {f["rationType"]: f for f in c.get("/api/ai/demand-forecast", headers=env["official"]).json()["data"]}
    assert forecast["Rice"]["last30DaysKg"] == 5 and forecast["Rice"]["predictedNext30DaysKg"] == 5
    risks = c.get("/api/ai/inventory-risk", headers=env["shop"]).json()["data"]
    rice = next(r for r in risks if r["rationType"] == "Rice")
    assert rice["currentStatus"] == "NORMAL" and rice["averageDailyConsumption"] == 0.36
    assert rice["explanation"] == "Consuming ~0.4 kg/day over the last 14 days; 95 kg on hand."
    assert {r["shopId"] for r in risks} == {1}   # a shop owner only ever gets their own shop
    queue = c.get("/api/ai/queue-prediction", headers=env["official"]).json()["data"]
    assert queue[0]["pendingInQueue"] == 0
    center = c.get("/api/ai/intelligence-center", headers=env["official"]).json()["data"]
    assert center["isSyntheticData"] is True and center["shopsRequiringAttention"] == 0
    assert c.get("/api/ai/intelligence-center", headers=env["shop"]).status_code == 403
    assert c.get("/api/ai/demand-forecast", headers=env["citizen"]).status_code == 403


def test_repeated_scans_raise_one_alert(env):
    token = book(env).json()["data"]
    payload = qr_payload(env, token["id"])
    for _ in range(4):
        env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": payload})
    c = env["client"]
    c.get("/api/ai/intelligence-center", headers=env["official"])
    c.get("/api/ai/intelligence-center", headers=env["official"])   # a second run does not duplicate it
    alerts = c.get("/api/ai/alerts", headers=env["official"]).json()["data"]
    assert [a["alertType"] for a in alerts] == ["RepeatedQrScan"] and alerts[0]["status"] == int(AIAlertStatus.Open)
    ben = my_beneficiary_id(env)
    insight = c.get(f"/api/ai/beneficiaries/{ben}/insight", headers=env["shop"]).json()["data"]
    assert insight["riskLevel"] == "Medium" and "4 repeated QR scan attempts in the last 24 hours" in insight["reasons"]
    with session() as db:
        assert db.scalar(select(AIInsight.InsightType)) == "BeneficiaryRisk"


def test_shop_insight_is_scoped(env):
    c = env["client"]
    assert c.get("/api/ai/shops/1/insight", headers=env["shop"]).json()["data"]["recommendation"] == "No immediate action required."
    assert c.get("/api/ai/shops/2/insight", headers=env["shop"]).status_code == 403
    assert c.get("/api/ai/shops/99/insight", headers=env["official"]).status_code == 404


# ---------------------------------------------------------------- optional AI service

def test_analytics_fall_back_when_the_ai_service_is_not_configured(env):
    c = env["client"]
    data = c.get("/api/ai/analytics/forecast", headers=env["official"]).json()["data"]
    assert data["available"] is False and data["source"] == "fallback" and data["errorCode"] == "AI_NOT_CONFIGURED"
    assert isinstance(data["fallback"], list)
    risk = c.get("/api/ai/analytics/risk", headers=env["official"]).json()["data"]
    assert risk["source"] == "unavailable" and risk["fallback"] is None
    assert c.get("/api/health").json() == {"system": "DEGRADED", "api": "UP", "database": "CONNECTED", "ai": "NOT_CONFIGURED",
                                           "qrConfigured": True}


SEEN: list[httpx.Request] = []
ALERTS = [
    {"dedup_key": "stock:1:1", "alert_type": "StockoutRisk", "severity": "High", "shop_id": 1, "ration_type": 1, "score": 140,
     "title": "Rice may run out", "description": "d", "metadata": {"days": 2}},
    {"dedup_key": "stock:2:1", "alert_type": "StockoutRisk", "severity": "Low", "shop_id": 2, "description": "other shop"},
    {"dedup_key": "", "alert_type": "Broken", "severity": "High"},
    {"alert_type": "NoKey", "severity": "Medium"},
]


def fake_ai(request: httpx.Request) -> httpx.Response:
    SEEN.append(request)
    if request.url.path == "/v1/alerts":
        return httpx.Response(200, json={"data": {"items": ALERTS}})
    if request.url.path == "/v1/forecast":
        return httpx.Response(200, json={"data": {"series": [1, 2, 3]}})
    if request.url.path == "/v1/ocr/extract":
        return httpx.Response(200, json={"data": {"fields": {"name": "A"}}})
    return httpx.Response(503, json={"error_code": "AI_BUSY", "message": "busy"})


@pytest.mark.parametrize("env", [{"ai_handler": fake_ai}], indirect=True)
def test_live_ai_analytics_alert_sync_and_ocr(env):
    SEEN.clear()
    c = env["client"]
    data = c.get("/api/ai/analytics/forecast", params={"horizonDays": 500, "lang": "xx"}, headers=env["shop"]).json()["data"]
    assert data == {"available": True, "source": "python-ai", "data": {"series": [1, 2, 3]}, "fallback": None, "errorCode": None, "message": None}
    sent = SEEN[-1]
    assert sent.headers["X-Api-Key"] == "unit-test-ai-key"
    assert dict(sent.url.params) == {"shop_id": "1", "lang": "en", "horizon_days": "90"}   # shop owner scoped, clamped
    assert c.get("/api/ai/analytics/shops", headers=env["official"]).json()["data"]["errorCode"] == "AI_BUSY"

    first = c.post("/api/ai/alerts/sync", headers=env["official"]).json()["data"]
    assert (first["created"], first["updated"], first["rejected"]) == (2, 0, 2)
    again = c.post("/api/ai/alerts/sync", headers=env["official"]).json()["data"]
    assert (again["created"], again["updated"]) == (0, 2)   # dedup: refreshed, not duplicated
    assert c.get("/api/ai/alerts/active", headers=env["official"]).json()["data"]["sync"]["skipped"] is True   # throttled
    mine = c.get("/api/ai/alerts/list", headers=env["shop"]).json()["data"]
    assert [a["shopName"] for a in mine] == ["Satnavari FPS"]   # never another shop's alert
    alert = mine[0]
    assert alert["severity"] == "HIGH" and alert["score"] == 100 and alert["rationType"] == "Rice" and alert["metadata"] == {"days": 2}
    assert c.get("/api/ai/alerts/shop/2", headers=env["shop"]).status_code == 403
    assert c.post(f"/api/ai/alerts/{alert['id']}/resolve", headers=env["shop"], json={"status": "Resolved"}).status_code == 403
    assert c.post(f"/api/ai/alerts/{alert['id']}/resolve", headers=env["official"], json={"status": "Open"}).status_code == 400
    r = c.post(f"/api/ai/alerts/{alert['id']}/resolve", headers=env["official"], json={"status": "Resolved", "note": " checked "})
    assert r.status_code == 200 and r.json()["data"]["status"] == "Resolved" and r.json()["data"]["resolutionNote"] == "checked"
    assert c.get("/api/ai/alerts/list?status=bogus", headers=env["official"]).json()["errorCode"] == "INVALID_STATUS"
    with session() as db:
        assert db.scalar(select(AIAlert).where(AIAlert.Id == alert["id"])).ResolvedByUserId == 60
        assert db.scalar(select(AuditLog.Action).where(AuditLog.Action == "AI_ALERT_RESOLVED")) is not None

    png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
    r = c.post("/api/ocr/extract", headers=env["shop"], files={"file": ("card.png", png, "image/png")})
    assert r.status_code == 200 and r.json()["data"]["data"] == {"fields": {"name": "A"}}
    assert c.post("/api/ocr/extract", headers=env["shop"], files={"file": ("a.gif", b"GIF89a", "image/gif")}).json()["errorCode"] == "INVALID_IMAGE"
    assert c.post("/api/ocr/extract", headers=env["citizen"], files={"file": ("card.png", png, "image/png")}).status_code == 403


# ---------------------------------------------------------------- government / admin

def test_government_dashboard_statistics_and_reports(env):
    collect(env)
    c = env["client"]
    dash = c.get("/api/admin/dashboard", headers=env["official"]).json()["data"]
    assert (dash["totalBeneficiaries"], dash["todayCollections"], dash["rationDistributedTodayKg"]) == (1, 1, 8)
    stats = c.get("/api/admin/statistics", headers=env["official"]).json()["data"]
    assert stats["tokensGenerated"] == 1 and stats["collectionEfficiencyPercent"] == 100
    assert stats["shopPerformance"] == [{"shopId": 1, "shopName": "Satnavari FPS", "totalTokens": 1, "completedTokens": 1, "efficiencyPercent": 100}]
    assert stats["fromDate"].endswith("T00:00:00")
    reports = {r["reportName"]: r["recordCount"] for r in c.get("/api/admin/reports", headers=env["official"]).json()["data"]}
    assert reports["QR Verification Report"] == 1 and reports["Daily Collection Report"] == 1
    assert c.get("/api/admin/statistics?fromDate=nope", headers=env["official"]).status_code == 400
    assert c.get("/api/admin/dashboard", headers=env["shop"]).status_code == 403


def test_users_list(env):
    c = env["client"]
    shops = c.get("/api/admin/users?role=shopowner", headers=env["official"]).json()["data"]
    assert [u["fullName"] for u in shops] == ["Other Owner", "Shop Owner"]
    assert c.get("/api/admin/users?role=King", headers=env["official"]).status_code == 400


def test_map(env):
    book(env)
    c = env["client"]
    markers = c.get("/api/shops/map", headers=env["official"]).json()["data"]
    assert {m["id"] for m in markers} == {1, 2} and markers[0]["dataSource"] == "SYNTHETIC_DEMO"
    assert markers[0]["todayBookings"] == 1 and markers[0]["eligibleBeneficiaries"] == 1
    assert c.get("/api/shops/map?inventoryStatus=critical", headers=env["official"]).json()["data"] == []
    detail = c.get("/api/shops/1/location", headers=env["official"]).json()["data"]
    assert detail["operatorName"] == "Shop Owner" and len(detail["inventory"]) == 2
    analytics = c.get("/api/government/map/analytics", headers=env["official"]).json()["data"]
    assert analytics["totalShops"] == 2 and analytics["demandHeatmap"] == [{"lat": 0, "lng": 0, "intensity": 1}]
    assert c.get("/api/shops/map", headers=env["shop"]).status_code == 403


def test_database_viewer_is_read_only_and_paged(env):
    collect(env)
    c = env["client"]
    assert c.get("/api/admin/database/tables", headers=env["official"]).json()["data"][0] == "beneficiaries"
    for table in ("beneficiaries", "familyMembers", "tokens", "collections", "inventory", "aiInsights", "auditLogs"):
        r = c.get(f"/api/admin/database/{table}", headers=env["official"])
        assert r.status_code == 200, table
        assert set(r.json()["data"]) == {"items", "totalCount", "page", "pageSize"}
    inv = c.get("/api/admin/database/inventory?page=1&pageSize=1", headers=env["official"]).json()["data"]
    assert inv["totalCount"] == 2 and len(inv["items"]) == 1 and inv["items"][0]["available"] == 95
    missing = c.get("/api/admin/database/passwords", headers=env["official"])
    assert missing.status_code == 404 and missing.json()["success"] is False
    ben = c.get("/api/admin/synthetic-data/beneficiaries?search=900000000&aadhaarStatus=Verified", headers=env["official"]).json()["data"]
    assert ben["totalCount"] == 1 and ben["items"][0]["aadhaarStatus"] == "Verified"   # mobile search on this screen only
    assert c.get("/api/admin/database/beneficiaries?search=900000000", headers=env["official"]).json()["data"]["totalCount"] == 0
    assert c.get("/api/admin/synthetic-data/beneficiaries?aadhaarStatus=Failed", headers=env["official"]).json()["data"]["totalCount"] == 0
    assert c.get("/api/admin/database/tokens", headers=env["shop"]).status_code == 403
