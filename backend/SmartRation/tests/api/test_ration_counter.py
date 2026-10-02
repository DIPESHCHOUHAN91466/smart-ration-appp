"""Migrated booking + shop-counter flow (formerly served by the C# API), end to end on SQLite:

citizen books a slot -> token + signed QR -> shop scans it -> OTP fallback -> collection confirmed in one
transaction (stock, ledger, receipt, audit) -> retry with the same Idempotency-Key returns the same receipt.
All data here is synthetic; the QR secret and passwords are test-only values.
"""

from __future__ import annotations

from decimal import Decimal

from ration_world import book, qr_payload, session
from sqlalchemy import select

from app.database.enums import InventoryMovementType, MobileVerificationStatus, TokenStatus, VerificationAction
from app.database.models import (
    AuditLog,
    Beneficiary,
    Inventory,
    InventoryMovement,
    MobileVerification,
    RationCollection,
    TimeSlot,
    Token,
    User,
    VerificationAuditLog,
)
from app.security.tokens import TokenUser, create_access_token
from app.utils.time import utc_now

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

def test_scan_verifies_a_signed_qr(env):
    token = book(env).json()["data"]
    r = env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": qr_payload(env, token["id"])})
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
    payload = qr_payload(env, token["id"])
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
    result = env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": qr_payload(env, token["id"])}).json()["data"]
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
    scan = c.post("/api/qr/scan", headers=env["shop"], json={"qrData": qr_payload(env, token["id"])}).json()["data"]
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


def test_stock_changes_retried_with_the_same_key_are_recorded_once(env):
    c = env["client"]
    deliver = {**env["shop"], "Idempotency-Key": "stock-req-1"}
    first = c.post("/api/inventory/1/receive", headers=deliver, json={"quantity": 20, "reference": "CH-2026/002"})
    again = c.post("/api/inventory/1/receive", headers=deliver, json={"quantity": 20, "reference": "CH-2026/002"})
    assert first.status_code == again.status_code == 200
    assert first.json()["data"]["availableQuantity"] == again.json()["data"]["availableQuantity"] == 120

    write_off = {**env["shop"], "Idempotency-Key": "stock-req-2"}
    assert c.post("/api/inventory/1/damage", headers=write_off, json={"quantity": 115}).json()["data"]["availableQuantity"] == 5
    # The retry succeeds even though 115 more would no longer be in stock: it is the same write-off.
    r = c.post("/api/inventory/1/damage", headers=write_off, json={"quantity": 115})
    assert r.status_code == 200 and r.json()["data"]["availableQuantity"] == 5

    # The same key for a different change is refused, and nothing is recorded.
    r = c.post("/api/inventory/1/receive", headers=deliver, json={"quantity": 7})
    assert r.status_code == 409 and r.json()["errorCode"] == "IDEMPOTENCY_KEY_REUSED"
    r = c.post("/api/inventory/1/damage", headers=deliver, json={"quantity": 20})
    assert r.status_code == 409 and r.json()["errorCode"] == "IDEMPOTENCY_KEY_REUSED"
    long_key = {**env["shop"], "Idempotency-Key": "k" * 65}
    assert c.post("/api/inventory/1/receive", headers=long_key, json={"quantity": 1}).json()["errorCode"] == "INVALID_IDEMPOTENCY_KEY"

    # Without a key every request is a new movement, as before.
    for _ in range(2):
        assert c.post("/api/inventory/1/receive", headers=env["shop"], json={"quantity": 1}).status_code == 200
    with session() as db:
        assert db.get(Inventory, 1).AvailableQuantity == 7
        moves = db.scalars(select(InventoryMovement).order_by(InventoryMovement.Id)).all()
        assert [(m.MovementType, m.Quantity, m.IdempotencyKey) for m in moves] == [
            (InventoryMovementType.Received, 20, "stock-req-1"), (InventoryMovementType.Damaged, 115, "stock-req-2"),
            (InventoryMovementType.Received, 1, None), (InventoryMovementType.Received, 1, None)]


def test_verification_audit_is_for_officials_only(env):
    token = book(env).json()["data"]
    env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": qr_payload(env, token["id"])})
    assert env["client"].get("/api/audit/verification", headers=env["shop"]).status_code == 403
    rows = env["client"].get("/api/audit/verification", headers=env["official"]).json()["data"]
    assert rows and all("qrData" not in row for row in rows)


def test_routes_answer_under_v1_too(env):
    assert env["client"].get("/api/v1/ration/items", headers=env["citizen"]).status_code == 200


def test_beneficiary_exists_for_registered_citizen(env):
    with session() as db:
        assert db.scalar(select(Beneficiary.BeneficiaryCode)).startswith("BEN-DEMO-")
