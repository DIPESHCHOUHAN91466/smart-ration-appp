"""The shop counter and stock: QR scanner, dashboard and queue, beneficiary verification (QR / OTP),
collection confirmation, inventory, notifications and the verification audit trail.

Migrated from the C# QrController (scan), ShopController, VerificationController,
RationCollectionController (confirm), InventoryController, NotificationsController and AuditController.
"""

from __future__ import annotations

import math
import re
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies.auth import OFFICIALS, STAFF, Actor, actor
from app.api.routes._common import idempotency_key, json_body, settings_of
from app.core.body import Body
from app.core.errors import BadRequest, ok
from app.database.connection import get_db
from app.database.enums import UserRole
from app.security.rate_limit import rate_limit
from app.services import (
    booking_service,
    collection_service,
    inventory_service,
    notification_service,
    otp_service,
    shop_service,
    verification_audit_service,
    verification_service,
)
from app.utils.masking import mask_mobile
from app.utils.time import utc_now

router = APIRouter(prefix="/api", tags=["shop counter"])

scan_limit = Depends(rate_limit("scan", lambda s: s.scan_rate_limit_per_minute))
otp_limit = Depends(rate_limit("otp", lambda s: s.otp_rate_limit_per_minute))
shop_owner = actor(UserRole.ShopOwner)
staff = actor(*STAFF)
any_user = actor()

REFERENCE = re.compile(r"^[A-Za-z0-9\-/_. ]*$")


def _key(request: Request, *, strict: bool) -> str | None:
    key = idempotency_key(request)
    if key and len(key) > 64:
        if strict:
            raise BadRequest("Idempotency-Key must be at most 64 characters.", "INVALID_IDEMPOTENCY_KEY")
        return None
    return key


# ---------------------------------------------------------------- scanner, dashboard, queue

@router.post("/qr/scan", summary="Global QR scanner: every outcome as a structured status", dependencies=[scan_limit])
def qr_scan(request: Request, body: Body = Depends(json_body), who: Actor = Depends(shop_owner), db: Session = Depends(get_db)):
    data = body.string("QrData", required=True, max_length=2048)
    body.raise_if_invalid()
    result = shop_service.scan(db, settings_of(request).qr_secret, who, data)
    return ok(result, result["message"])


@router.get("/shop/dashboard", summary="Today's counts and stock at my shop")
def shop_dashboard(who: Actor = Depends(shop_owner), db: Session = Depends(get_db)):
    return ok(shop_service.dashboard(db, who))


@router.get("/shop/queue", summary="Today's queue at my shop")
def shop_queue(who: Actor = Depends(shop_owner), db: Session = Depends(get_db)):
    return ok(booking_service.today_queue(db, who))


@router.post("/shop/collection/complete", summary="Mark a queued token collected (same checks as QR verification)")
def shop_complete(request: Request, body: Body = Depends(json_body), who: Actor = Depends(shop_owner), db: Session = Depends(get_db)):
    token_id = body.integer("TokenId", required=True)
    body.raise_if_invalid()
    return ok(shop_service.complete_collection(db, who, token_id, _key(request, strict=False)), "Collection marked complete")


# ---------------------------------------------------------------- beneficiary verification

@router.get("/verification/qr/{reference}", summary="Verify a beneficiary from a scanned QR", dependencies=[scan_limit])
def verify_qr(reference: str, request: Request, who: Actor = Depends(shop_owner), db: Session = Depends(get_db)):
    return ok(verification_service.verify_by_qr(db, settings_of(request).qr_secret, who, reference), "Beneficiary verified")


@router.post("/verification/otp/request", summary="Send a one-time code to the beneficiary's mobile", dependencies=[otp_limit])
def otp_request(request: Request, body: Body = Depends(json_body), who: Actor = Depends(shop_owner), db: Session = Depends(get_db)):
    mobile = body.string("MobileNumber", required=True, is_phone=True)
    body.raise_if_invalid()
    settings = settings_of(request)
    otp = otp_service.request_for_mobile(db, settings, mobile, who.user_id)
    return ok({"otpVerificationId": otp.Id, "mobileMasked": mask_mobile(mobile),
               "expiresInMinutes": math.ceil((otp.ExpiresAt - utc_now()).total_seconds() / 60),
               # The demo code is shown only in synthetic development mode (refused at startup in production).
               "demoOtpValue": settings.demo_otp_value if settings.demo_otp_enabled else None}, "OTP sent")


@router.post("/verification/otp/verify", summary="Check the one-time code and verify the beneficiary", dependencies=[otp_limit])
def otp_verify(body: Body = Depends(json_body), who: Actor = Depends(shop_owner), db: Session = Depends(get_db)):
    otp_id = body.integer("OtpVerificationId", required=True)
    code = body.string("Code", required=True, max_length=6, min_length=6)
    body.raise_if_invalid()
    otp = otp_service.verify(db, otp_id, code)
    if who.ration_shop_id is None:
        raise BadRequest("Your account is not linked to a ration shop.")
    return ok(verification_service.verify_beneficiary_at_shop(db, who, otp.BeneficiaryId, who.ration_shop_id, "OTP"), "OTP verified")


@router.post("/ration/collection/confirm", summary="Issue the ration: stock, token, receipt and audit in one transaction")
def collection_confirm(request: Request, body: Body = Depends(json_body), who: Actor = Depends(shop_owner), db: Session = Depends(get_db)):
    token_id = body.integer("TokenId", required=True)
    method = body.string("VerificationMethod")
    body.raise_if_invalid()
    key = _key(request, strict=True)
    return ok(collection_service.confirm(db, who, token_id, method or "QR", key), "Ration collection confirmed")


# ---------------------------------------------------------------- inventory

def _movement(body: Body) -> tuple[Decimal, str | None, str | None]:
    qty = body.decimal("Quantity", minimum=Decimal("0.01"), maximum=Decimal("1000000"))
    reference = body.string("Reference", max_length=64)
    if reference and not REFERENCE.match(reference):
        body.errors.append("Reference: Reference may only contain letters, numbers and - / _ .")
    note = body.string("Note", max_length=256)
    body.raise_if_invalid()
    return qty, reference, note


@router.get("/inventory", summary="Stock lines (my shop, or any shop for officials)")
def inventory_list(shopId: int | None = None, who: Actor = Depends(staff), db: Session = Depends(get_db)):
    return ok(inventory_service.list_for(db, who, shopId))


@router.post("/inventory", summary="Add a stock line to a shop")
def inventory_create(body: Body = Depends(json_body), who: Actor = Depends(staff), db: Session = Depends(get_db)):
    shop_id = body.integer("RationShopId", required=True)
    ration_type = body.string("RationType", required=True)
    available = body.decimal("AvailableQuantity", minimum=Decimal(0))
    minimum = body.decimal("MinimumStockLevel", minimum=Decimal(0))
    body.raise_if_invalid()
    return ok(inventory_service.create(db, who, shop_id, ration_type, available, minimum), "Inventory record created")


@router.put("/inventory/{inventory_id}", summary="Correct a stock balance / minimum level")
def inventory_update(inventory_id: int, body: Body = Depends(json_body), who: Actor = Depends(staff), db: Session = Depends(get_db)):
    available = body.decimal("AvailableQuantity", minimum=Decimal(0))
    minimum = body.decimal("MinimumStockLevel", minimum=Decimal(0))
    body.raise_if_invalid()
    return ok(inventory_service.update(db, who, inventory_id, available, minimum), "Inventory updated")


@router.post("/inventory/{inventory_id}/receive", summary="Record a stock delivery")
def inventory_receive(inventory_id: int, request: Request, body: Body = Depends(json_body), who: Actor = Depends(staff),
                      db: Session = Depends(get_db)):
    qty, reference, note = _movement(body)
    key = _key(request, strict=True)
    return ok(inventory_service.receive(db, who, inventory_id, qty, reference, note, key), "Stock received")


@router.post("/inventory/{inventory_id}/damage", summary="Write off damaged stock")
def inventory_damage(inventory_id: int, request: Request, body: Body = Depends(json_body), who: Actor = Depends(staff),
                     db: Session = Depends(get_db)):
    qty, reference, note = _movement(body)
    key = _key(request, strict=True)
    return ok(inventory_service.damage(db, who, inventory_id, qty, reference, note, key), "Damaged stock recorded")


# ---------------------------------------------------------------- notifications and verification audit

@router.get("/notifications", summary="My notifications")
def notifications(who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(notification_service.list_for(db, who))


@router.post("/notifications/read", summary="Mark my notifications read")
def notifications_read(body: Body = Depends(json_body), who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    if body.raw("NotificationIds") is None:
        body.errors.append("NotificationIds: The NotificationIds field is required.")
    ids = body.integers("NotificationIds", min_items=1)
    body.raise_if_invalid()
    notification_service.mark_read(db, who, ids)
    return ok(None, "Notifications marked as read")


@router.get("/audit/verification", summary="Verification audit trail (officials)")
def verification_audit(shopId: int | None = None, beneficiaryId: int | None = None, status: str | None = None, take: int = 100,
                       _: Actor = Depends(actor(*OFFICIALS)), db: Session = Depends(get_db)):
    return ok(verification_audit_service.query(db, shopId, beneficiaryId, status, take))
