"""Signed QR codes for bookings, and parsing whatever a shop's scanner reads.

Two signed forms, both HMAC-SHA256 with QR_SECRET (never the JWT key), byte-compatible with every QR
code issued so far:

  reference  SRQR-{tokenId}-{first 16 hex chars of HMAC("{tokenId}:{tokenNumber}")}
             (stored on the booking; also what an operator types when a camera can't read the QR)
  envelope   JSON {version, project, type, reference, token, issuedAt, expiresAt, signature}
             signature = first 32 hex chars of HMAC("envelope:" + those fields joined by "|")
             (what the QR image on "My Token & QR" encodes; valid until the end of the booked day)

The QR never contains personal data. Every failure carries a stable error code (QrScanStatus) so the
scanner can show a specific, translated result.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound, ServiceUnavailable
from app.database.enums import TokenStatus, UserRole
from app.database.models import TimeSlot, Token
from app.services._db import require
from app.services.mappers import token_dto
from app.utils.time import utc_now

VERSION, PROJECT, TYPE = "1.0", "SMART_RATION_HSD2C", "RATION_TOKEN"
REQUIRED_FIELDS = ["version", "project", "type", "reference", "token", "issuedAt", "expiresAt", "signature"]


class QrScanStatus:
    VERIFIED = "VERIFIED"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_PROJECT = "INVALID_PROJECT"
    INVALID_TYPE = "INVALID_TYPE"
    MISSING_FIELDS = "MISSING_FIELDS"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    EXPIRED = "EXPIRED"
    TOKEN_NOT_FOUND = "TOKEN_NOT_FOUND"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    ALREADY_COLLECTED = "ALREADY_COLLECTED"
    WRONG_SHOP = "WRONG_SHOP"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


@dataclass(frozen=True)
class ParsedQr:
    reference: str
    claimed_token_number: str | None


def _secret(secret: str) -> bytes:
    if not secret:
        raise ServiceUnavailable("QR codes are not configured on this server (QR_SECRET is missing).", "QR_NOT_CONFIGURED")
    return secret.encode("utf-8")


def compute_reference(secret: str, token_id: int, token_number: str) -> str:
    digest = hmac.new(_secret(secret), f"{token_id}:{token_number}".encode(), hashlib.sha256).hexdigest().upper()
    return f"SRQR-{token_id}-{digest[:16]}"


def _sign_envelope(secret: str, f: dict[str, str]) -> str:
    canonical = "envelope:" + "|".join(f[k] for k in ("version", "project", "type", "reference", "token", "issuedAt", "expiresAt"))
    return hmac.new(_secret(secret), canonical.encode(), hashlib.sha256).hexdigest().upper()[:32]


def _utc_text(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_signed_payload(secret: str, token: Token, slot: TimeSlot) -> str:
    # Seeded showcase tokens keep their fixed SRQR-DEMO alias; everything else gets the derived reference.
    stored = token.QRCodeValue or ""
    reference = stored if stored.startswith("SRQR-DEMO-") else compute_reference(secret, token.Id, token.TokenNumber)
    day = slot.SlotDate.replace(hour=0, minute=0, second=0, microsecond=0)
    envelope = {"version": VERSION, "project": PROJECT, "type": TYPE, "reference": reference, "token": token.TokenNumber,
                "issuedAt": _utc_text(token.CreatedAt), "expiresAt": _utc_text(day + timedelta(days=1))}
    envelope["signature"] = _sign_envelope(secret, envelope)
    # Same text as System.Text.Json: compact, keys in this order.
    return json.dumps(envelope, separators=(",", ":"), ensure_ascii=False)


def parse_scanned(secret: str, raw_qr: str | None) -> ParsedQr:
    raw = (raw_qr or "").strip()
    if not raw or len(raw) > 2048:
        raise BadRequest("QR code is not recognized.", QrScanStatus.INVALID_FORMAT)
    # Bare reference: typed manually, or a QR printed before the envelope existed.
    if not raw.startswith(("{", "[")):
        if not raw.startswith("SRQR-"):
            raise BadRequest("This QR code does not belong to the Smart Ration system.", QrScanStatus.INVALID_PROJECT)
        return ParsedQr(raw, None)
    try:
        doc = json.loads(raw)
        if not isinstance(doc, dict):
            raise ValueError
    except ValueError:
        raise BadRequest("QR code is malformed.", QrScanStatus.INVALID_FORMAT) from None
    fields = {k: v for k, v in doc.items() if isinstance(v, str)}
    # Project/type first so an unrelated JSON QR gets the clearest message.
    if fields.get("project") != PROJECT:
        raise BadRequest("This QR code does not belong to the Smart Ration system.", QrScanStatus.INVALID_PROJECT)
    if any(not (fields.get(f) or "").strip() for f in REQUIRED_FIELDS):
        raise BadRequest("Required QR information is missing.", QrScanStatus.MISSING_FIELDS)
    if fields["type"] != TYPE:
        raise BadRequest("This QR code is not a ration token.", QrScanStatus.INVALID_TYPE)
    if fields["version"] != VERSION:
        raise BadRequest("This QR code version is not supported.", QrScanStatus.UNSUPPORTED_VERSION)
    # Constant-time compare so the signature can't be probed byte by byte.
    if not hmac.compare_digest(_sign_envelope(secret, fields).encode(), fields["signature"].upper().encode()):
        raise BadRequest("QR code signature is invalid.", QrScanStatus.INVALID_SIGNATURE)
    # Expiry is only trusted after the signature check proves the server issued it.
    try:
        expires = datetime.fromisoformat(fields["expiresAt"].replace("Z", "+00:00"))
        if expires.tzinfo is not None:
            expires = expires.astimezone(UTC).replace(tzinfo=None)
    except ValueError:
        raise BadRequest("QR code is malformed.", QrScanStatus.INVALID_FORMAT) from None
    if utc_now() > expires:
        raise BadRequest("This collection QR code is no longer valid.", QrScanStatus.EXPIRED)
    return ParsedQr(fields["reference"], fields["token"])


def _resolve_reference(db: Session, secret: str, actor: Actor, reference: str) -> Token:
    parts = reference.split("-")
    if len(parts) == 3 and parts[0] == "SRQR" and parts[1].isdigit():
        token = db.get(Token, int(parts[1]))
        if token is None:
            raise NotFound("QR code does not match any booking.", QrScanStatus.TOKEN_NOT_FOUND)
        if not hmac.compare_digest(compute_reference(secret, token.Id, token.TokenNumber), reference):
            raise BadRequest("QR code signature is invalid.", QrScanStatus.INVALID_SIGNATURE)
    elif reference.startswith("SRQR-DEMO-"):
        # Fixed showcase aliases seeded onto specific demo tokens: an exact-match lookup, never a bypass.
        token = db.scalar(select(Token).where(Token.QRCodeValue == reference))
        if token is None:
            raise NotFound("QR code does not match any booking.", QrScanStatus.TOKEN_NOT_FOUND)
    else:
        raise BadRequest("QR code is not recognized.", QrScanStatus.INVALID_FORMAT)
    if actor.role == UserRole.ShopOwner and token.RationShopId != actor.ration_shop_id:
        raise Forbidden("This token belongs to another ration shop.", QrScanStatus.WRONG_SHOP)
    return token


def resolve_token_for_verification(db: Session, secret: str, actor: Actor, qr_value: str | None) -> tuple[Token, ParsedQr]:
    parsed = parse_scanned(secret, qr_value)
    token = _resolve_reference(db, secret, actor, parsed.reference)
    # The envelope is signed, so a mismatch means the reference and token number belong to different bookings.
    if parsed.claimed_token_number is not None and parsed.claimed_token_number != token.TokenNumber:
        raise BadRequest("QR code signature is invalid.", QrScanStatus.INVALID_SIGNATURE)
    return token, parsed


# ---------------------------------------------------------------- endpoints

def _own_or_official(actor: Actor, token: Token, what: str) -> None:
    if token.UserId != actor.user_id and actor.role not in (UserRole.Admin, UserRole.GovernmentOfficial):
        raise Forbidden(f"You can only {what} for your own token.")


def regenerate(db: Session, secret: str, actor: Actor, token_id: int) -> str:
    token = db.get(Token, token_id)
    if token is None:
        raise NotFound("Token not found.")
    _own_or_official(actor, token, "generate a QR code")
    if token.Status in (TokenStatus.Completed, TokenStatus.Cancelled):
        raise BadRequest(f"Cannot generate a QR code for a token in {TokenStatus(token.Status).name} status.")
    token.QRCodeValue = compute_reference(secret, token.Id, token.TokenNumber)
    db.commit()
    return token.QRCodeValue


def payload_for_token(db: Session, secret: str, actor: Actor, token_id: int) -> str:
    token = db.get(Token, token_id)
    if token is None:
        raise NotFound("Token not found.")
    _own_or_official(actor, token, "view the QR code")
    return build_signed_payload(secret, token, require(db, TimeSlot, token.TimeSlotId, "Time slot not found."))


def verify(db: Session, secret: str, actor: Actor, qr_value: str) -> dict:
    token, _ = resolve_token_for_verification(db, secret, actor, qr_value)
    if token.Status == TokenStatus.Completed:
        raise Conflict("This QR code has already been used for collection.")
    if token.Status == TokenStatus.Cancelled:
        raise Conflict("This booking was cancelled.")
    return token_dto(db, token)
