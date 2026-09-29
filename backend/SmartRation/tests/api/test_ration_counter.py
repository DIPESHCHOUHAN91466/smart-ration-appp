"""Migrated booking + shop-counter flow (formerly served by the C# API), end to end on SQLite:

citizen books a slot -> token + signed QR -> shop scans it -> OTP fallback -> collection confirmed in one
transaction (stock, ledger, receipt, audit) -> retry with the same Idempotency-Key returns the same receipt.
All data here is synthetic; the QR secret and passwords are test-only values.
"""

from __future__ import annotations

from datetime import time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.database.base import Base
from app.database.connection import get_engine, get_session_factory
from app.database.enums import InventoryMovementType, MobileVerificationStatus, TokenStatus, VerificationAction
from app.database.models import (
    AuditLog,
    Beneficiary,
    Inventory,
    InventoryMovement,
    MobileVerification,
    RationCollection,
    RationItem,
    RationScheme,
    RationShop,
    SchemeEntitlementItem,
    TimeSlot,
    Token,
    User,
    VerificationAuditLog,
)
from app.security.tokens import TokenUser, create_access_token
from app.utils.dotnet import midnight
from app.utils.time import utc_now

QR_SECRET = "unit-test-qr-secret-0123456789abcdef"
TEST_PASSWORD = "Unit-Test-Only-9!"   # a test fixture value, never a real password


def session():
    return get_session_factory()()


@pytest.fixture
def env(make_client):
    client = make_client(lambda r: None, qr_secret=QR_SECRET)
    settings = client.app.state.settings
    Base.metadata.create_all(get_engine())
    today = midnight(utc_now())
    with session() as db:
        now = utc_now()
        db.add_all([
            RationShop(Id=1, ShopName="Satnavari FPS", ShopCode="FPS-001", Address="a", District="Nagpur", State="MH",
                       Latitude=0, Longitude=0, IsActive=True, CreatedAt=now),
            RationShop(Id=2, ShopName="Other FPS", ShopCode="FPS-002", Address="b", District="Nagpur", State="MH",
                       Latitude=0, Longitude=0, IsActive=True, CreatedAt=now),
            RationScheme(Id=1, SchemeCode="DEMO-NFSA", Name="NFSA", Description="", IsActive=True),
            SchemeEntitlementItem(RationSchemeId=1, RationType=1, QuotaPerEligibleMemberPerMonth=Decimal(5)),
            SchemeEntitlementItem(RationSchemeId=1, RationType=2, QuotaPerEligibleMemberPerMonth=Decimal(3)),
            RationItem(Id=1, RationType=1, Name="Rice", VernacularName="Chawal", Unit="kg", StandardQuotaPerBooking=Decimal(5), IsActive=True),
            RationItem(Id=2, RationType=2, Name="Wheat", VernacularName="Gehu", Unit="kg", StandardQuotaPerBooking=Decimal(3), IsActive=True),
            Inventory(Id=1, RationShopId=1, RationType=1, AvailableQuantity=Decimal(100), AllocatedQuantity=Decimal(0),
                      MinimumStockLevel=Decimal(10), UpdatedAt=now),
            Inventory(Id=2, RationShopId=1, RationType=2, AvailableQuantity=Decimal(50), AllocatedQuantity=Decimal(0),
                      MinimumStockLevel=Decimal(10), UpdatedAt=now),
            User(Id=50, FullName="Shop Owner", Email="shop@example.com", MobileNumber="9000000051", PasswordHash="x", Role=2,
                 IsActive=True, CreatedAt=now, RationShopId=1),
            User(Id=51, FullName="Other Owner", Email="shop2@example.com", MobileNumber="9000000052", PasswordHash="x", Role=2,
                 IsActive=True, CreatedAt=now, RationShopId=2),
            User(Id=60, FullName="Official", Email="gov@example.com", MobileNumber="9000000061", PasswordHash="x", Role=3,
                 IsActive=True, CreatedAt=now),
            TimeSlot(Id=1, RationShopId=1, SlotDate=today, StartTime=time(9), EndTime=time(9, 5), Capacity=2, BookedCount=0),
            TimeSlot(Id=2, RationShopId=1, SlotDate=today + timedelta(days=1), StartTime=time(9), EndTime=time(9, 5), Capacity=1, BookedCount=0),
            TimeSlot(Id=3, RationShopId=1, SlotDate=today - timedelta(days=1), StartTime=time(9), EndTime=time(9, 5), Capacity=2, BookedCount=0),
        ])
        db.commit()

    r = client.post("/api/auth/register", json={"fullName": "Asha Patil", "email": "asha@example.com",
                                                "mobileNumber": "9000000001", "password": TEST_PASSWORD})
    assert r.status_code == 200, r.text
    citizen = r.json()["data"]["accessToken"]

    def bearer(user_id: int, email: str, role: str, shop: int | None) -> dict:
        return {"Authorization": f"Bearer {create_access_token(TokenUser(user_id, email, role, role, shop), settings)[0]}"}

    return {"client": client, "citizen": {"Authorization": f"Bearer {citizen}"},
            "shop": bearer(50, "shop@example.com", "ShopOwner", 1), "other_shop": bearer(51, "shop2@example.com", "ShopOwner", 2),
            "official": bearer(60, "gov@example.com", "GovernmentOfficial", None)}


def book(env, slot_id=1, items=None):
    return env["client"].post("/api/ration/bookings", headers=env["citizen"], json={
        "rationShopId": 1, "timeSlotId": slot_id,
        "items": items or [{"rationType": "Rice", "quantity": 5}, {"rationType": "Wheat", "quantity": 3}]})


# ---------------------------------------------------------------- catalog, slots, booking

def test_items_show_stock_and_remaining_entitlement(env):
    r = env["client"].get("/api/ration/items?shopId=1", headers=env["citizen"])
    assert r.status_code == 200
    rice = next(i for i in r.json()["data"] if i["rationType"] == "Rice")
    assert rice["availableQuantity"] == 100 and rice["eligibleQuantity"] == 5   # 1 eligible member x 5 kg


def test_slots_list_and_status(env):
    r = env["client"].get("/api/slots", params={"shopId": 1, "date": f"{utc_now():%Y-%m-%d}"}, headers=env["citizen"])
    assert r.status_code == 200
    assert [s["id"] for s in r.json()["data"]] == [1]
    assert r.json()["data"][0]["startTime"] == "09:00:00"


def test_booking_creates_token_and_takes_a_slot_place(env):
    r = book(env)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["message"] == "Booking created and token generated"
    token = body["data"]
    assert token["tokenNumber"] == f"SR-{utc_now():%Y}-{token['id']:06d}"
    assert token["status"] == "Confirmed" and token["qrCodeValue"].startswith(f"SRQR-{token['id']}-")
    with session() as db:
        assert db.get(TimeSlot, 1).BookedCount == 1
        assert db.scalar(select(AuditLog).where(AuditLog.Action == "BOOKING_CREATED")) is not None


def test_booking_validation_and_rules(env):
    c = env["client"]
    r = c.post("/api/ration/bookings", headers=env["citizen"], json={"rationShopId": 1, "timeSlotId": 1, "items": []})
    assert r.status_code == 400 and "Items: Select at least one ration item." in r.json()["errors"]
    r = c.post("/api/ration/bookings", headers=env["citizen"], json={"rationShopId": 1, "timeSlotId": 1,
                                                                     "items": [{"rationType": "Rice", "quantity": 0}]})
    assert r.status_code == 400 and r.json()["errors"] == ["Items[0].Quantity: The field Quantity must be between 0.01 and 1000."]
    assert book(env, slot_id=3).json()["message"] == "Cannot book a time slot in the past."
    assert book(env, items=[{"rationType": "Rice", "quantity": 6}]).status_code == 400          # above per-visit quota
    assert book(env).status_code == 200
    assert book(env).status_code == 409                                                        # duplicate in the same slot


def test_slot_capacity_is_enforced(env):
    assert book(env, slot_id=2).status_code == 200
    with session() as db:   # a second citizen for the one remaining place
        db.add(User(Id=70, FullName="B", Email="b@example.com", MobileNumber="9000000070", PasswordHash="x", Role=1,
                    IsActive=True, CreatedAt=utc_now()))
        db.commit()
    settings = env["client"].app.state.settings
    other = {"Authorization": f"Bearer {create_access_token(TokenUser(70, 'b@example.com', 'B', 'RuralUser', None), settings)[0]}"}
    r = env["client"].post("/api/ration/bookings", headers=other, json={
        "rationShopId": 1, "timeSlotId": 2, "items": [{"rationType": "Rice", "quantity": 1}]})
    assert r.status_code == 409 and r.json()["message"] == "This time slot is full. Please choose another slot."


def test_cancel_frees_the_place_and_reschedule_moves_it(env):
    token = book(env).json()["data"]
    r = env["client"].put(f"/api/ration/bookings/{token['id']}", headers=env["citizen"], json={"timeSlotId": 2})
    assert r.status_code == 200 and r.json()["data"]["timeSlotId"] == 2
    assert env["client"].delete(f"/api/ration/bookings/{token['id']}", headers=env["citizen"]).json()["message"] == "Booking cancelled"
    with session() as db:
        assert (db.get(TimeSlot, 1).BookedCount, db.get(TimeSlot, 2).BookedCount) == (0, 0)
        assert db.get(Token, token["id"]).Status == TokenStatus.Cancelled


def test_bookings_are_private_to_their_owner_and_shop(env):
    token = book(env).json()["data"]
    assert env["client"].get(f"/api/ration/bookings/{token['id']}", headers=env["shop"]).status_code == 200
    assert env["client"].get(f"/api/ration/bookings/{token['id']}", headers=env["other_shop"]).status_code == 403
    assert env["client"].get("/api/ration/bookings", headers=env["other_shop"]).json()["data"] == []
    assert env["client"].post("/api/ration/bookings", headers=env["shop"], json={}).status_code == 403   # citizens only
    assert env["client"].get("/api/ration/bookings").status_code == 401


# ---------------------------------------------------------------- QR, scan, verification, collection

def _qr(env, token_id):
    r = env["client"].get(f"/api/qr/payload/{token_id}", headers=env["citizen"])
    assert r.status_code == 200
    return r.json()["data"]


def test_scan_verifies_a_signed_qr(env):
    token = book(env).json()["data"]
    r = env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": _qr(env, token["id"])})
    assert r.status_code == 200
    result = r.json()["data"]
    assert result["status"] == "VERIFIED" and result["verified"] is True and r.json()["message"] == "QR verified successfully"
    v = result["verification"]
    assert v["aadhaarVerification"]["aadhaarMasked"].startswith("XXXX-XXXX-")
    assert v["verificationSummary"]["overallStatus"] == "READY_FOR_RATION_COLLECTION"
    with session() as db:
        audit = db.scalars(select(VerificationAuditLog.Action)).all()
        assert VerificationAction.QrScanned in audit and VerificationAction.BeneficiaryVerified in audit


def test_scan_rejects_a_tampered_or_foreign_qr(env):
    token = book(env).json()["data"]
    payload = _qr(env, token["id"])
    tampered = payload.replace(token["tokenNumber"], "SR-2000-000001")
    r = env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": tampered})
    assert r.status_code == 200 and r.json()["data"]["verified"] is False
    assert r.json()["data"]["status"] == "INVALID_SIGNATURE"
    r = env["client"].post("/api/qr/scan", headers=env["other_shop"], json={"qrData": payload})
    assert r.json()["data"]["status"] == "WRONG_SHOP"
    scan = lambda text: env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": text}).json()["data"]["status"]  # noqa: E731
    assert scan("hello") == "INVALID_PROJECT" and scan("{not json") == "INVALID_FORMAT"
    assert env["client"].post("/api/qr/scan", headers=env["citizen"], json={"qrData": payload}).status_code == 403


def test_blocked_reason_when_mobile_is_not_verified(env):
    token = book(env).json()["data"]
    with session() as db:
        mobile = db.scalar(select(MobileVerification))
        mobile.Status = int(MobileVerificationStatus.NotVerified)
        db.commit()
    result = env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": _qr(env, token["id"])}).json()["data"]
    assert result["status"] == "NOT_ELIGIBLE" and result["message"] == "Mobile OTP verification required."


def test_collection_is_atomic_audited_and_idempotent(env):
    token = book(env).json()["data"]
    c, headers = env["client"], {**env["shop"], "Idempotency-Key": "counter-1-req-1"}
    r = c.post("/api/ration/collection/confirm", headers=headers, json={"tokenId": token["id"], "verificationMethod": "QR"})
    assert r.status_code == 200, r.text
    receipt = r.json()["data"]
    assert receipt["collectionCode"].startswith("COL-DEMO-") and receipt["totalQuantityKg"] == 8
    assert receipt["issuedItems"] == [{"rationType": "Rice", "quantity": 5}, {"rationType": "Wheat", "quantity": 3}]
    with session() as db:
        assert db.get(Inventory, 1).AvailableQuantity == 95 and db.get(Inventory, 1).AllocatedQuantity == 5
        moves = db.scalars(select(InventoryMovement)).all()
        assert {(m.RationType, m.MovementType, m.Quantity, m.BalanceAfter) for m in moves} == {
            (1, InventoryMovementType.Distributed, 5, 95), (2, InventoryMovementType.Distributed, 3, 47)}
        assert db.get(Token, token["id"]).Status == TokenStatus.Completed

    # A retry of the same request returns the same receipt and issues nothing more.
    again = c.post("/api/ration/collection/confirm", headers=headers, json={"tokenId": token["id"], "verificationMethod": "QR"})
    assert again.status_code == 200 and again.json()["data"]["collectionCode"] == receipt["collectionCode"]
    # A new request for the used token is refused.
    r = c.post("/api/ration/collection/confirm", headers=env["shop"], json={"tokenId": token["id"]})
    assert r.status_code == 409 and r.json()["message"] == "This token has already been used for collection."
    with session() as db:
        assert db.get(Inventory, 1).AvailableQuantity == 95 and len(db.scalars(select(RationCollection)).all()) == 1
    scan = c.post("/api/qr/scan", headers=env["shop"], json={"qrData": _qr(env, token["id"])}).json()["data"]
    assert scan["status"] == "ALREADY_COLLECTED"


def test_collection_issues_nothing_when_any_item_is_short(env):
    token = book(env).json()["data"]
    with session() as db:
        db.get(Inventory, 2).AvailableQuantity = Decimal(1)   # wheat short, rice fine
        db.commit()
    r = env["client"].post("/api/ration/collection/confirm", headers=env["shop"], json={"tokenId": token["id"]})
    assert r.status_code == 409 and r.json()["errorCode"] == "INSUFFICIENT_STOCK"
    with session() as db:
        assert db.get(Inventory, 1).AvailableQuantity == 100      # rice untouched: all-or-nothing
        assert db.get(Token, token["id"]).Status == TokenStatus.Confirmed
        assert db.scalars(select(InventoryMovement)).all() == []


def test_other_shop_cannot_collect(env):
    token = book(env).json()["data"]
    r = env["client"].post("/api/ration/collection/confirm", headers=env["other_shop"], json={"tokenId": token["id"]})
    assert r.status_code == 403


def test_otp_fallback_verifies_the_beneficiary(env):
    book(env)
    c = env["client"]
    r = c.post("/api/verification/otp/request", headers=env["shop"], json={"mobileNumber": "9000000001"})
    assert r.status_code == 200, r.text
    otp = r.json()["data"]
    assert otp["mobileMasked"] == "******0001" and otp["expiresInMinutes"] == 5 and otp["demoOtpValue"] == "123456"
    # Cooldown: an immediate second request is refused.
    assert c.post("/api/verification/otp/request", headers=env["shop"], json={"mobileNumber": "9000000001"}).json()["errorCode"] == "OTP_COOLDOWN"
    wrong = c.post("/api/verification/otp/verify", headers=env["shop"], json={"otpVerificationId": otp["otpVerificationId"], "code": "000000"})
    assert wrong.status_code == 400 and wrong.json()["message"] == "Incorrect OTP. 2 attempt(s) remaining."
    r = c.post("/api/verification/otp/verify", headers=env["shop"], json={"otpVerificationId": otp["otpVerificationId"], "code": "123456"})
    assert r.status_code == 200 and r.json()["message"] == "OTP verified"
    assert r.json()["data"]["verificationSummary"]["overallStatus"] == "READY_FOR_RATION_COLLECTION"
    with session() as db:   # only a hash is stored
        from app.database.models import OtpVerification
        assert "123456" not in db.scalar(select(OtpVerification.OtpHash))


def test_queue_complete_uses_the_same_pipeline(env):
    token = book(env).json()["data"]
    queue = env["client"].get("/api/shop/queue", headers=env["shop"]).json()["data"]
    assert [t["id"] for t in queue] == [token["id"]]
    r = env["client"].post("/api/shop/collection/complete", headers=env["shop"], json={"tokenId": token["id"]})
    assert r.status_code == 200 and r.json()["data"]["status"] == "Completed"
    with session() as db:
        assert db.scalar(select(RationCollection.VerificationMethod)) == "QUEUE"
    dash = env["client"].get("/api/shop/dashboard", headers=env["shop"]).json()["data"]
    assert (dash["todayTotalTokens"], dash["todayCompleted"], dash["todayPending"]) == (1, 1, 0)


# ---------------------------------------------------------------- inventory, notifications, audit

def test_inventory_movements_and_permissions(env):
    c = env["client"]
    r = c.post("/api/inventory/1/receive", headers=env["shop"], json={"quantity": 20, "reference": "CH-2026/001"})
    assert r.status_code == 200 and r.json()["data"]["availableQuantity"] == 120
    r = c.post("/api/inventory/1/damage", headers=env["shop"], json={"quantity": 500})
    assert r.status_code == 400 and r.json()["errorCode"] == "INSUFFICIENT_STOCK"
    assert c.post("/api/inventory/1/receive", headers=env["shop"], json={"quantity": 1, "reference": "<script>"}).status_code == 400
    assert c.post("/api/inventory/1/receive", headers=env["other_shop"], json={"quantity": 1}).status_code == 403
    assert c.get("/api/inventory", headers=env["citizen"]).status_code == 403
    # A correction below the minimum notifies the shop owner.
    r = c.put("/api/inventory/1", headers=env["shop"], json={"availableQuantity": 5, "minimumStockLevel": 10})
    assert r.status_code == 200
    notes = c.get("/api/notifications", headers=env["shop"]).json()["data"]
    assert any(n["title"] == "Low stock alert" for n in notes)
    with session() as db:
        kinds = [m.MovementType for m in db.scalars(select(InventoryMovement).order_by(InventoryMovement.Id))]
        assert kinds == [InventoryMovementType.Received, InventoryMovementType.Adjustment]


def test_verification_audit_is_for_officials_only(env):
    token = book(env).json()["data"]
    env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": _qr(env, token["id"])})
    assert env["client"].get("/api/audit/verification", headers=env["shop"]).status_code == 403
    rows = env["client"].get("/api/audit/verification", headers=env["official"]).json()["data"]
    assert rows and all("qrData" not in row for row in rows)


def test_routes_answer_under_v1_too(env):
    assert env["client"].get("/api/v1/ration/items", headers=env["citizen"]).status_code == 200


def test_beneficiary_exists_for_registered_citizen(env):
    with session() as db:
        assert db.scalar(select(Beneficiary.BeneficiaryCode)).startswith("BEN-DEMO-")
