"""Download my data (N17, DPDP Act 2023): a person's own records only, never credentials or other people's data."""

from __future__ import annotations

import json

from ration_world import book
from sqlalchemy import select

from app.database.connection import get_session_factory
from app.database.models import AuditLog
from app.services.data_export_service import FIELDS

# Columns deliberately NOT exported. A new column must be added either to FIELDS (exported) or here (reviewed and
# withheld) — this test fails until someone decides.
WITHHELD = {
    "User": {"PasswordHash", "TotpSecret", "TotpLastStep", "RationShopId"},
    "Beneficiary": {"Id", "ProfilePhotoUrl", "UserId", "FamilyId", "DataSource"},
    "Family": {"Id", "DataSource"},
    "FamilyMember": {"Id", "FamilyId", "DataSource"},
    "Token": {"Id", "UserId", "TimeSlotId", "QRCodeValue"},
    "TokenItem": {"Id", "TokenId"},
    "RationCollection": {"Id", "TokenId", "BeneficiaryId", "OperatorUserId", "IdempotencyKey"},
    "Grievance": {"Id", "UserId", "IdempotencyKey", "ResolvedByUserId"},
    "Notification": {"Id", "UserId"},
    "AuditLog": {"Id", "UserId", "EntityName", "EntityId", "Role"},
    "AadhaarVerification": {"Id", "BeneficiaryId", "AadhaarReferenceId"},
    "MobileVerification": {"Id", "BeneficiaryId"},
    "PassbookVerification": {"Id", "BeneficiaryId"},
}


def test_every_column_is_either_exported_or_deliberately_withheld():
    for model, (exported, _) in FIELDS.items():
        columns = {c.name for c in model.__table__.columns}
        assert set(exported) | WITHHELD[model.__name__] == columns, model.__name__
        assert not set(exported) & WITHHELD[model.__name__], model.__name__


def test_a_citizen_downloads_their_own_records(env):
    assert book(env).status_code == 200
    r = env["client"].get("/api/users/me/export", headers=env["citizen"])
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    data = r.json()["data"]
    assert data["format"] == "smart-ration-personal-data" and data["account"]["Email"] == "asha@example.com"
    assert data["account"]["Role"] == "RuralUser" and data["beneficiary"]["BeneficiaryCode"]
    assert data["family"]["members"] and data["bookings"][0]["Status"] in ("Pending", "Confirmed")
    assert {i["RationType"] for i in data["bookings"][0]["items"]} == {"Rice", "Wheat"}
    assert any(e["Action"] == "REGISTER" for e in data["accountEvents"])
    raw = r.text
    for forbidden in ("$argon2", "$2b$", "PasswordHash", "TotpSecret", "SRQR-", "IdempotencyKey"):
        assert forbidden not in raw, forbidden
    with get_session_factory()() as db:
        assert db.scalar(select(AuditLog.Action).where(AuditLog.Action == "DATA_EXPORTED")) == "DATA_EXPORTED"


def test_the_export_holds_nobody_elses_data(env):
    r = env["client"].post("/api/auth/register", json={"fullName": "Ravi Kale", "email": "ravi@example.com",
                                                       "mobileNumber": "9000000002", "password": "Kite-River-Lamp-42"})
    assert r.status_code == 200
    raw = json.dumps(env["client"].get("/api/users/me/export", headers=env["citizen"]).json())
    assert "ravi@example.com" not in raw and "Ravi Kale" not in raw and "9000000002" not in raw


def test_staff_get_their_account_without_a_beneficiary_record(env):
    data = env["client"].get("/api/users/me/export", headers=env["shop"]).json()["data"]
    assert data["account"]["Role"] == "ShopOwner" and data["beneficiary"] is None and data["family"] is None


def test_sign_in_is_required_and_exports_are_rate_limited(env):
    assert env["client"].get("/api/users/me/export").status_code == 401        # counts towards the 5 per minute too
    codes = [env["client"].get("/api/users/me/export", headers=env["citizen"]).status_code for _ in range(5)]
    assert codes[:4] == [200] * 4 and codes[4] == 429
