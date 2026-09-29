"""QR_SECRET configuration and the signed booking QR, end to end.

Covers: the API refusing to start without a usable QR_SECRET; health reporting only a yes/no; booking ->
server-signed QR; the shop owner's scan/verify accepting a genuine QR and rejecting forged, tampered,
expired, unknown-booking and already-used ones; the secret and raw Aadhaar never leaving the server.
All values here are test-only.
"""

from __future__ import annotations

import json
from datetime import timedelta

import httpx
import pytest
from py_testkit import make_settings
from ration_world import QR_SECRET, book, qr_payload, session
from sqlalchemy import select

from app.database.models import AadhaarVerification, Token
from app.main import create_app
from app.services import qr_service
from app.utils.time import utc_now


def resign(fields: dict, secret: str = QR_SECRET) -> str:
    """What only a holder of QR_SECRET can do: produce a valid signature for these fields."""
    body = {k: v for k, v in fields.items() if k != "signature"}
    body["signature"] = qr_service._sign_envelope(secret, body)
    return json.dumps(body, separators=(",", ":"))


def scan(env, qr: str, who: str = "shop") -> dict:
    r = env["client"].post("/api/qr/scan", headers=env[who], json={"qrData": qr})
    assert r.status_code == 200, r.text
    return r.json()["data"]


# ---------------------------------------------------------------- configuration

@pytest.mark.parametrize("value, reason", [
    ("", "not set"),
    ("replace_with_a_secure_random_secret", "placeholder"),
    ("secret", "placeholder"),
    ("short-but-not-empty", "too short"),
])
def test_api_refuses_to_start_without_a_usable_qr_secret(tmp_path, value, reason):
    with pytest.raises(RuntimeError) as error:
        create_app(make_settings(tmp_path, qr_secret=value))
    assert reason in str(error.value) and "secrets.token_urlsafe(64)" in str(error.value)


def test_health_says_whether_qr_is_configured_but_never_the_secret(env, make_client):
    c = make_client(lambda r: httpx.Response(200, json={}), qr_secret=QR_SECRET)
    for path in ("/health", "/api/health"):
        r = c.get(path)
        assert r.json()["qrConfigured"] is True, path
        assert QR_SECRET not in r.text


def test_settings_repr_hides_the_secret(tmp_path):
    assert QR_SECRET not in repr(make_settings(tmp_path, qr_secret=QR_SECRET))


# ---------------------------------------------------------------- booking -> signed QR

def test_confirm_and_generate_token_persists_the_booking_and_a_signed_qr(env):
    r = book(env)
    assert r.status_code == 200, r.text
    token = r.json()["data"]
    assert token["status"] == "Confirmed" and token["qrCodeValue"] == qr_service.compute_reference(QR_SECRET, token["id"], token["tokenNumber"])
    with session() as db:
        saved = db.get(Token, token["id"])
        assert saved is not None and saved.TokenNumber == token["tokenNumber"] and saved.QRCodeValue == token["qrCodeValue"]

    payload = qr_payload(env, token["id"])
    fields = json.loads(payload)
    assert set(fields) == {"version", "project", "type", "reference", "token", "issuedAt", "expiresAt", "signature"}
    assert fields["signature"] == qr_service._sign_envelope(QR_SECRET, fields)
    # Only an opaque reference and the token number: no Aadhaar, mobile, name, family or password.
    with session() as db:
        last_four = db.scalar(select(AadhaarVerification.AadhaarMasked))[-4:]
    for sensitive in ("9000000001", "Asha", last_four, "aadhaar", "password"):
        assert sensitive.lower() not in payload.lower()
    assert QR_SECRET not in payload and QR_SECRET not in r.text


def test_only_the_owner_can_fetch_their_qr(env):
    token = book(env).json()["data"]
    assert env["client"].get(f"/api/qr/payload/{token['id']}", headers=env["shop"]).status_code == 403
    assert env["client"].get(f"/api/qr/payload/{token['id']}").status_code == 401


# ---------------------------------------------------------------- scan / verify

def test_genuine_qr_is_accepted_with_masked_identity(env):
    token = book(env).json()["data"]
    result = scan(env, qr_payload(env, token["id"]))
    assert result["status"] == "VERIFIED" and result["tokenNumber"] == token["tokenNumber"]
    v = result["verification"]
    assert v["aadhaarVerification"]["aadhaarMasked"].startswith("XXXX-XXXX-")
    assert v["booking"]["shopName"] == "Satnavari FPS" and v["entitlement"]["schemeCode"] == "DEMO-NFSA"
    assert v["family"]["members"] and v["verificationSummary"]["overallStatus"] == "READY_FOR_RATION_COLLECTION"
    text = json.dumps(result)
    assert QR_SECRET not in text and "9000000001" not in text

    r = env["client"].post("/api/qr/verify", headers=env["shop"], json={"qrCodeValue": qr_payload(env, token["id"])})
    assert r.status_code == 200 and r.json()["data"]["tokenNumber"] == token["tokenNumber"]


def test_signature_from_another_secret_is_rejected(env):
    token = book(env).json()["data"]
    forged = resign(json.loads(qr_payload(env, token["id"])), secret="an-attacker-guess-0123456789abcdefghij")
    assert scan(env, forged)["status"] == "INVALID_SIGNATURE"


def test_tampered_payload_is_rejected(env):
    token = book(env).json()["data"]
    fields = json.loads(qr_payload(env, token["id"]))
    for key, value in (("expiresAt", "2099-01-01T00:00:00Z"), ("token", "SR-2026-999999"), ("reference", "SRQR-1-0000000000000000")):
        tampered = json.dumps({**fields, key: value})
        assert scan(env, tampered)["status"] == "INVALID_SIGNATURE", key


def test_expired_qr_is_rejected(env):
    token = book(env).json()["data"]
    fields = json.loads(qr_payload(env, token["id"]))
    expired = resign({**fields, "expiresAt": (utc_now() - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")})
    assert scan(env, expired)["status"] == "EXPIRED"
    r = env["client"].post("/api/qr/verify", headers=env["shop"], json={"qrCodeValue": expired})
    assert r.status_code == 400 and r.json()["errorCode"] == "EXPIRED"


def test_unknown_booking_is_rejected(env):
    token = book(env).json()["data"]
    fields = json.loads(qr_payload(env, token["id"]))
    ghost = resign({**fields, "reference": qr_service.compute_reference(QR_SECRET, 99999, "SR-2026-099999"), "token": "SR-2026-099999"})
    assert scan(env, ghost)["status"] == "TOKEN_NOT_FOUND"
    r = env["client"].post("/api/qr/verify", headers=env["shop"], json={"qrCodeValue": ghost})
    assert r.status_code == 404 and r.json()["errorCode"] == "TOKEN_NOT_FOUND"


def test_used_and_cancelled_bookings_are_rejected(env):
    token = book(env).json()["data"]
    qr = qr_payload(env, token["id"])
    assert env["client"].post("/api/ration/collection/confirm", headers=env["shop"], json={"tokenId": token["id"]}).status_code == 200
    assert scan(env, qr)["status"] == "ALREADY_COLLECTED"
    assert env["client"].post("/api/qr/verify", headers=env["shop"], json={"qrCodeValue": qr}).status_code == 409

    second = book(env, slot_id=2).json()["data"]
    qr2 = qr_payload(env, second["id"])
    env["client"].delete(f"/api/ration/bookings/{second['id']}", headers=env["citizen"])
    assert scan(env, qr2)["status"] == "BOOKING_CANCELLED"


def test_scanning_needs_a_shop_owner(env):
    token = book(env).json()["data"]
    qr = qr_payload(env, token["id"])
    assert env["client"].post("/api/qr/scan", headers=env["citizen"], json={"qrData": qr}).status_code == 403
    assert env["client"].post("/api/qr/scan", json={"qrData": qr}).status_code == 401
    assert scan(env, qr, who="other_shop")["status"] == "WRONG_SHOP"


def test_login_still_works(env):
    from ration_world import TEST_PASSWORD
    r = env["client"].post("/api/auth/login", json={"email": "asha@example.com", "password": TEST_PASSWORD})
    assert r.status_code == 200 and r.json()["data"]["accessToken"]
    assert env["client"].post("/api/auth/login", json={"email": "asha@example.com", "password": "wrong-password"}).status_code == 401


def test_scan_reports_its_own_duration_only(env):
    token = book(env).json()["data"]
    r = env["client"].post("/api/qr/scan", headers=env["shop"], json={"qrData": qr_payload(env, token["id"])})
    timing = r.headers["Server-Timing"]
    assert timing.startswith("app;dur=") and float(timing.split("=")[1]) >= 0   # a number, nothing else
    assert QR_SECRET not in timing


def test_scan_returns_member_details_without_inventing_any(env):
    from app.database.models import Beneficiary, FamilyMember
    with session() as db:
        family_id = db.scalar(select(Beneficiary.FamilyId))
        db.add_all([
            FamilyMember(FamilyId=family_id, FullName="Son Test", Age=8, Relationship=3, Eligibility=1, DataSource="SYNTHETIC_DEMO"),
            FamilyMember(FamilyId=family_id, FullName="Parent Test", Age=61, Relationship=5, Eligibility=2, DataSource="SYNTHETIC_DEMO"),
        ])
        db.commit()
    token = book(env).json()["data"]
    v = scan(env, qr_payload(env, token["id"]))["verification"]
    members = {m["fullName"]: m for m in v["family"]["members"]}
    head = next(m for m in members.values() if m["isHead"])
    assert head["aadhaarMasked"].startswith("XXXX-XXXX-") and head["identityVerified"] is True and head["gender"]
    son, parent = members["Son Test"], members["Parent Test"]
    assert son["gender"] == "Male" and son["aadhaarMasked"] is None and son["identityVerified"] is None
    assert parent["gender"] is None                                   # "Parent" does not imply a gender: not guessed
    assert v["family"]["familySize"] == 3 and v["family"]["eligibleMemberCount"] == 2
    # Each eligible member's share = the scheme quota per member (rice 5 kg, wheat 3 kg); none for ineligible.
    assert {i["rationType"]: i["quantity"] for i in son["monthlyEntitlement"]} == {"Rice": 5, "Wheat": 3}
    assert parent["monthlyEntitlement"] == []
    assert all(len(m["aadhaarMasked"] or "XXXX-XXXX-0000") == 14 for m in members.values())   # never a full number
