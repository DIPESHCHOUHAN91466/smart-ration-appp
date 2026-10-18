"""One-time passwords: the fallback when a QR code can't be scanned.

Only a SHA-256 hash of each code is stored. Only the newest code for a beneficiary is valid; a new one
can be requested after a cooldown; a code expires after OTP_EXPIRY_MINUTES and after OTP_MAX_ATTEMPTS
wrong tries. DEMO mode (DEMO_OTP_ENABLED, refused outside development) issues a fixed code instead of a
random one. The SMS text contains the code, so it is never logged — only the masked number.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import smtplib
import ssl
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from email.message import EmailMessage

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.core.errors import BadRequest, Forbidden, NotFound, ServiceUnavailable
from app.database.enums import OtpStatus
from app.database.models import Beneficiary, OtpVerification, User
from app.security.rate_limit import TooManyRequests
from app.services import audit_service
from app.services._db import require
from app.utils.masking import mask_mobile
from app.utils.time import business_day_utc, business_today, utc_now

log = logging.getLogger("smartration.otp")


@dataclass(frozen=True)
class SmsResult:
    sent: bool
    provider: str
    error: str | None = None


def send_sms(settings: Settings, phone: str, message: str) -> SmsResult:
    """'mock': sends nothing (development / synthetic demo). 'http': JSON POST to a DLT-registered gateway."""
    if settings.sms_provider.lower() != "http":
        log.info("[MOCK SMS] Not sent", extra={"fields": {"to": mask_mobile(phone), "chars": len(message), "id": f"mock-{uuid.uuid4().hex}"}})
        return SmsResult(True, "Mock")
    if not settings.sms_base_url or not settings.sms_api_key:
        return SmsResult(False, "Http", "SMS gateway is not configured.")
    try:
        response = httpx.post(settings.sms_base_url, json={"to": phone, "sender": settings.sms_sender_id, "message": message},
                              headers={"Authorization": f"Bearer {settings.sms_api_key}"}, timeout=10)
    except httpx.HTTPError as exc:
        log.warning("SMS gateway unreachable", extra={"fields": {"to": mask_mobile(phone), "error": type(exc).__name__}})
        return SmsResult(False, "Http", "SMS gateway unreachable.")
    if response.status_code >= 400:
        log.warning("SMS gateway error", extra={"fields": {"to": mask_mobile(phone), "status": response.status_code}})
        return SmsResult(False, "Http", f"Gateway returned {response.status_code}.")
    return SmsResult(True, "Http")


def send_email(settings: Settings, to: str, subject: str, text: str) -> SmsResult:
    """Plain-text e-mail over SMTP with STARTTLS (port 587). Never logs the address or the message."""
    message = EmailMessage()
    message["From"] = f"Smart Ration <{settings.smtp_from or settings.smtp_username}>"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        log.warning("E-mail not sent", extra={"fields": {"error": type(exc).__name__}})
        return SmsResult(False, "Email", "E-mail could not be sent.")
    return SmsResult(True, "Email")


NO_DELIVERY = "One-time codes cannot be sent on this site yet. Please sign in with your password."


def ensure_delivery_available(settings: Settings) -> None:
    """Refuse a code request up front when nothing could deliver it (no SMS gateway, no SMTP, not development).
    Checked before any account lookup, so the answer is the same for every number (no account enumeration)."""
    if not settings.code_delivery_available:
        raise ServiceUnavailable(NO_DELIVERY, "SMS_UNAVAILABLE")


def deliver_code(settings: Settings, user: User, subject: str, text: str) -> SmsResult:
    """Sends a one-time code by SMS and, when SMTP is configured, also to the account's e-mail.
    With a real SMS gateway either channel is enough. With the mock SMS (no gateway: the synthetic demo) the
    e-mail is the only real delivery, so the code counts as sent only if the e-mail went out. Outside development
    the mock alone never counts as sent: nobody would receive the code."""
    sms = send_sms(settings, user.MobileNumber, text)
    if not settings.smtp_host.strip() or not (user.Email or "").strip():
        if sms.provider == "Mock" and not settings.is_development:
            return SmsResult(False, "Mock", "No SMS gateway or e-mail for this account.")
        return sms
    mail = send_email(settings, user.Email, subject, text)
    if settings.sms_provider.lower() == "http":
        return SmsResult(sms.sent or mail.sent, "Http+Email", None if sms.sent or mail.sent else sms.error)
    return mail


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest().upper()


NOT_SERVED = "No beneficiary with this mobile number can be served at your shop."


def request_for_mobile(db: Session, settings: Settings, mobile: str, requested_by: int,
                       can_serve: Callable[[int], bool] | None = None) -> OtpVerification:
    """A counter code for the beneficiary with this mobile. `can_serve` (the shop's visibility rule) limits it to
    beneficiaries the shop may serve; an unknown number and someone else's beneficiary get the same answer, so a shop
    account can neither text every citizen in the country nor learn which numbers are registered."""
    beneficiary_id = db.scalar(select(Beneficiary.Id).join(User, User.Id == Beneficiary.UserId)
                               .where(User.MobileNumber == mobile).limit(1))
    if beneficiary_id is None or (can_serve is not None and not can_serve(beneficiary_id)):
        raise NotFound(NOT_SERVED)
    return request(db, settings, beneficiary_id, requested_by)


CITIZEN_DAILY_LIMIT = "Too many one-time codes were requested for this beneficiary today. Please use QR verification or try again tomorrow."
SHOP_DAILY_LIMIT = "This shop has reached today's limit for one-time codes. Please use QR verification or try again tomorrow."


def _counter_codes_today(db: Session, *conditions) -> int:
    start, end = business_day_utc(business_today())   # the Indian calendar day, as UTC bounds
    return db.scalar(select(func.count()).select_from(OtpVerification).where(
        OtpVerification.CreatedAt >= start, OtpVerification.CreatedAt < end, *conditions)) or 0


def request(db: Session, settings: Settings, beneficiary_id: int, requested_by: int) -> OtpVerification:
    """A shop-counter code. Daily limits per Indian calendar day: OTP_COUNTER_DAILY_LIMIT per citizen (all shops
    together, so another shop can't add more) and OTP_COUNTER_SHOP_DAILY_LIMIT per shop account. The counts come from
    the codes stored in the database, with the shop's and the citizen's rows locked (always in that order) while they are
    checked and the new code is saved, so they hold across application instances and concurrent requests."""
    ensure_delivery_available(settings)
    db.scalar(select(User.Id).where(User.Id == requested_by).with_for_update())
    beneficiary = db.scalar(select(Beneficiary).where(Beneficiary.Id == beneficiary_id).with_for_update())
    if beneficiary is None:
        raise NotFound("Beneficiary not found.")
    if not beneficiary.IsActive or beneficiary.IsBlocked:
        raise Forbidden("This beneficiary account is not active.")
    now = utc_now()
    pending = db.scalars(select(OtpVerification).where(OtpVerification.BeneficiaryId == beneficiary_id,
                                                       OtpVerification.Status == int(OtpStatus.Pending))).all()
    newest = max(pending, key=lambda o: o.CreatedAt, default=None)
    if newest is not None:
        wait = settings.otp_resend_cooldown_seconds - int((now - newest.CreatedAt).total_seconds())
        if wait > 0:
            raise BadRequest(f"Please wait {wait} seconds before requesting another OTP.", "OTP_COOLDOWN")
    # The citizen's own sign-in codes (requested by themselves) have their own limit and are not counted here.
    blocked = None
    if _counter_codes_today(db, OtpVerification.RequestedByUserId == requested_by) >= settings.otp_counter_shop_daily_limit:
        blocked = (SHOP_DAILY_LIMIT, "OTP_SHOP_DAILY_LIMIT")
    elif _counter_codes_today(db, OtpVerification.BeneficiaryId == beneficiary_id,
                              OtpVerification.RequestedByUserId != beneficiary.UserId) >= settings.otp_counter_daily_limit:
        blocked = (CITIZEN_DAILY_LIMIT, "OTP_DAILY_LIMIT")
    if blocked is not None:
        # Audited without the number; the commit also releases the row locks.
        audit_service.record(db, requested_by, "COUNTER_OTP_LIMIT", "Beneficiary", str(beneficiary_id), details=blocked[1], result="BLOCKED")
        db.commit()
        raise TooManyRequests(*blocked)
    for old in pending:
        old.Status = int(OtpStatus.Expired)    # only the newest code is ever valid

    code = settings.demo_otp_value if settings.demo_otp_enabled else f"{secrets.randbelow(1_000_000):06d}"
    record = OtpVerification(BeneficiaryId=beneficiary_id, RequestedByUserId=requested_by, OtpHash=_hash(code), AttemptCount=0,
                             MaxAttempts=settings.otp_max_attempts, Status=int(OtpStatus.Pending), CreatedAt=now,
                             ExpiresAt=now + timedelta(minutes=settings.otp_expiry_minutes))
    db.add(record)
    db.commit()
    user = require(db, User, beneficiary.UserId, "User not found.")
    sent = deliver_code(settings, user, "Your Smart Ration verification code",
                        f"Your Smart Ration verification code is {code}. Valid for {settings.otp_expiry_minutes} minutes. "
                        "Do not share it.")
    if not sent.sent:
        record.Status = int(OtpStatus.Failed)   # an undeliverable code must not stay usable
        db.commit()
        raise ServiceUnavailable("Could not send the OTP right now. Please try again or use QR verification.", "SMS_UNAVAILABLE")
    return record


def verify(db: Session, otp_id: int, code: str, requested_by: int | None = None) -> OtpVerification:
    """`requested_by`: only the account that asked for this code may use it (ids are sequential); anyone else gets the
    same answer as for a missing id, and no attempt is counted."""
    record = db.scalar(select(OtpVerification).where(OtpVerification.Id == otp_id).with_for_update())
    if record is None or (requested_by is not None and record.RequestedByUserId != requested_by):
        raise NotFound("OTP request not found.")
    if record.Status != OtpStatus.Pending:
        raise BadRequest(f"This OTP request is already {OtpStatus(record.Status).name}.")
    if utc_now() > record.ExpiresAt:
        record.Status = int(OtpStatus.Expired)
        db.commit()
        raise BadRequest("OTP has expired. Please request a new one.")
    if record.AttemptCount >= record.MaxAttempts:
        record.Status = int(OtpStatus.Failed)
        db.commit()
        raise BadRequest("Maximum OTP attempts exceeded. Please request a new one.")
    if not secrets.compare_digest(_hash(code), record.OtpHash):
        record.AttemptCount += 1
        if record.AttemptCount >= record.MaxAttempts:
            record.Status = int(OtpStatus.Failed)
        db.commit()
        raise BadRequest(f"Incorrect OTP. {max(0, record.MaxAttempts - record.AttemptCount)} attempt(s) remaining.")
    record.Status = int(OtpStatus.Verified)
    record.VerifiedAt = utc_now()
    db.commit()
    return record
