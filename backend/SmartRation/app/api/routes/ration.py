"""Citizen booking flow: ration items, shops, time slots, bookings (tokens) and the token QR.

Migrated from the C# RationController, TokensController, SlotsController, ShopsController (list) and
QrController (generate / payload / verify). Same routes, bodies, roles and messages.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies.auth import STAFF, Actor, actor
from app.api.routes._common import json_body, parse_date, parse_timespan, settings_of
from app.core.body import Body, nested
from app.core.errors import ok
from app.database.connection import get_db
from app.database.enums import UserRole
from app.security.rate_limit import rate_limit
from app.services import booking_service, catalog_service, qr_service, slot_service

router = APIRouter(prefix="/api", tags=["ration"])

scan_limit = Depends(rate_limit("scan", lambda s: s.scan_rate_limit_per_minute))
any_user = actor()
citizen = actor(UserRole.RuralUser)
staff = actor(*STAFF)


def _booking_request(body: Body) -> tuple[int, int, list[tuple[str, Decimal]]]:
    shop_id = body.integer("RationShopId", required=True)
    slot_id = body.integer("TimeSlotId", required=True)
    raw_items = body.objects("Items", min_items=1, min_message="Select at least one ration item.")
    items, errors = [], []
    for item in nested(raw_items, "Items"):
        name = item.string("RationType", required=True)
        qty = item.decimal("Quantity", minimum=Decimal("0.01"), maximum=Decimal("1000"))
        errors += item.prefixed_errors
        items.append((name or "", qty))
    body.errors += errors
    body.raise_if_invalid()
    return shop_id, slot_id, items


# ---------------------------------------------------------------- catalog and shops

@router.get("/ration/items", summary="Active ration items (with stock / remaining entitlement when relevant)")
def ration_items(shopId: int | None = None, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(catalog_service.items(db, who, shopId))


@router.get("/shops", summary="Active ration shops")
def shops(_: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(catalog_service.active_shops(db))


# ---------------------------------------------------------------- bookings / tokens

@router.post("/ration/bookings", summary="Book a slot and generate a token")
def create_booking(request: Request, body: Body = Depends(json_body), who: Actor = Depends(citizen), db: Session = Depends(get_db)):
    shop_id, slot_id, items = _booking_request(body)
    return ok(booking_service.create(db, settings_of(request).qr_secret, who, shop_id, slot_id, items), "Booking created and token generated")


@router.post("/tokens/generate", summary="Book a slot and generate a token (alias)")
def generate_token(request: Request, body: Body = Depends(json_body), who: Actor = Depends(citizen), db: Session = Depends(get_db)):
    shop_id, slot_id, items = _booking_request(body)
    return ok(booking_service.create(db, settings_of(request).qr_secret, who, shop_id, slot_id, items), "Token generated")


@router.get("/ration/bookings", summary="My bookings / my shop's bookings / all bookings (by role)")
def list_bookings(who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(booking_service.list_for(db, who))


@router.get("/ration/bookings/{booking_id}", summary="One booking")
def get_booking(booking_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(booking_service.get(db, who, booking_id))


@router.get("/tokens/today", summary="Today's queue at my shop")
def tokens_today(who: Actor = Depends(actor(UserRole.ShopOwner)), db: Session = Depends(get_db)):
    return ok(booking_service.today_queue(db, who))


@router.get("/tokens/{token_id}", summary="One token")
def get_token(token_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(booking_service.get(db, who, token_id))


@router.put("/ration/bookings/{booking_id}", summary="Move a booking to another slot at the same shop")
def reschedule_booking(booking_id: int, body: Body = Depends(json_body), who: Actor = Depends(citizen), db: Session = Depends(get_db)):
    slot_id = body.integer("TimeSlotId", required=True)
    body.raise_if_invalid()
    return ok(booking_service.reschedule(db, who, booking_id, slot_id), "Booking rescheduled")


@router.delete("/ration/bookings/{booking_id}", summary="Cancel a booking (frees its slot place)")
def cancel_booking(booking_id: int, who: Actor = Depends(any_user), db: Session = Depends(get_db)):
    booking_service.cancel(db, who, booking_id)
    return ok(None, "Booking cancelled")


# ---------------------------------------------------------------- time slots

@router.get("/slots", summary="A shop's 5-minute slots for one day")
def list_slots(shopId: int = 0, date: str | None = None, _: Actor = Depends(any_user), db: Session = Depends(get_db)):
    return ok(slot_service.list_for_day(db, shopId, parse_date("date", date)))


@router.post("/slots", summary="Create a time slot")
def create_slot(body: Body = Depends(json_body), who: Actor = Depends(staff), db: Session = Depends(get_db)):
    shop_id = body.integer("RationShopId", required=True)
    day_raw = body.string("SlotDate", required=True)
    capacity = body.integer("Capacity", minimum=1, maximum=500)
    start = parse_timespan("StartTime", body.raw("StartTime"), body.errors)
    end = parse_timespan("EndTime", body.raw("EndTime"), body.errors)
    body.raise_if_invalid()
    day = parse_date("SlotDate", day_raw)
    return ok(slot_service.create(db, who, shop_id, day, start, end, 1 if capacity is None else capacity), "Time slot created")


@router.put("/slots/{slot_id}", summary="Change a slot's capacity")
def update_slot(slot_id: int, body: Body = Depends(json_body), who: Actor = Depends(staff), db: Session = Depends(get_db)):
    capacity = body.integer("Capacity", required=True, minimum=1, maximum=500)
    body.raise_if_invalid()
    return ok(slot_service.update_capacity(db, who, slot_id, capacity), "Time slot updated")


# ---------------------------------------------------------------- the token's QR

@router.post("/qr/generate", summary="(Re)issue the QR reference for my token")
def qr_generate(request: Request, body: Body = Depends(json_body), who: Actor = Depends(citizen), db: Session = Depends(get_db)):
    token_id = body.integer("TokenId", required=True)
    body.raise_if_invalid()
    return ok(qr_service.regenerate(db, settings_of(request).qr_secret, who, token_id), "QR code ready")


@router.get("/qr/payload/{token_id}", summary="Signed QR payload for my token (signed on the server)")
def qr_payload(token_id: int, request: Request,
               who: Actor = Depends(actor(UserRole.RuralUser, UserRole.GovernmentOfficial, UserRole.Admin)), db: Session = Depends(get_db)):
    return ok(qr_service.payload_for_token(db, settings_of(request).qr_secret, who, token_id), "QR payload ready")


@router.post("/qr/verify", summary="Check a scanned QR and return its token", dependencies=[scan_limit])
def qr_verify(request: Request, body: Body = Depends(json_body), who: Actor = Depends(staff), db: Session = Depends(get_db)):
    value = body.string("QrCodeValue", required=True)
    body.raise_if_invalid()
    return ok(qr_service.verify(db, settings_of(request).qr_secret, who, value), "QR code verified")

