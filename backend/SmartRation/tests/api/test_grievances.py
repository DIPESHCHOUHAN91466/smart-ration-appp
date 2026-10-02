"""Citizens' grievances: file with a reference number, retry safety, privacy checks, roles and officials' review.
All data is synthetic (the shared ration world in ration_world.py)."""

from __future__ import annotations

import re

from ration_world import session
from sqlalchemy import select

from app.database.enums import GrievanceStatus
from app.database.models import AuditLog, Grievance

COMPLAINT = {"category": "LessRation", "rationType": "Wheat", "description": "This month I received less wheat than my card shows.",
             "source": "ASSISTANT"}


def file(env, body=None, key=None):
    headers = {**env["citizen"], **({"Idempotency-Key": key} if key else {})}
    return env["client"].post("/api/grievances", headers=headers, json=body or COMPLAINT)


def test_a_citizen_files_a_complaint_and_gets_a_reference_number(env):
    r = file(env)
    assert r.status_code == 200, r.text
    g = r.json()["data"]
    assert re.fullmatch(r"GRV-\d{4}-\d{6}", g["referenceNumber"])
    assert (g["category"], g["rationType"], g["status"], g["source"]) == ("LessRation", "Wheat", "Submitted", "ASSISTANT")
    assert g["shopId"] is not None and g["shopName"]   # the citizen's own shop, from their ration card

    mine = env["client"].get("/api/grievances/mine", headers=env["citizen"]).json()["data"]
    assert [m["referenceNumber"] for m in mine] == [g["referenceNumber"]]
    notes = env["client"].get("/api/notifications", headers=env["citizen"]).json()["data"]
    assert any(n["type"] == "GrievanceUpdate" and g["referenceNumber"] in n["message"] for n in notes)
    with session() as db:   # audited, without the description
        details = db.scalars(select(AuditLog.Details).where(AuditLog.Action == "GRIEVANCE_SUBMITTED")).all()
        assert len(details) == 1 and "wheat" not in details[0].lower()


def test_a_retry_with_the_same_key_files_it_once(env):
    first, again = file(env, key="grv-req-1"), file(env, key="grv-req-1")
    assert first.status_code == again.status_code == 200
    assert first.json()["data"]["referenceNumber"] == again.json()["data"]["referenceNumber"]
    with session() as db:
        assert len(db.scalars(select(Grievance)).all()) == 1


def test_bad_or_private_input_is_refused(env):
    def code(body):
        r = file(env, {**COMPLAINT, **body})
        assert r.status_code == 400, r.text
        return r.json().get("errorCode")

    assert code({"description": "too short"}) == "DESCRIPTION_TOO_SHORT"
    assert code({"description": "My Aadhaar is 1234 5678 9012, please check my ration."}) == "SENSITIVE_DATA"
    assert code({"description": "The OTP 482913 did not work at the shop counter."}) == "SENSITIVE_DATA"
    assert file(env, {"category": "Other"}).status_code == 400   # description is required
    with session() as db:
        assert db.scalars(select(Grievance)).all() == []


def test_unknown_choices_are_refused(env):
    def code(body):
        r = file(env, {**COMPLAINT, **body})
        assert r.status_code == 400, r.text
        return r.json().get("errorCode")

    assert code({"category": "Nonsense"}) == "INVALID_CATEGORY"
    assert code({"rationType": "Gold"}) == "INVALID_ITEM"
    assert code({"source": "ROBOT"}) == "INVALID_SOURCE"


def test_filing_is_rate_limited(env):
    statuses = [file(env, key=f"grv-burst-{i}").status_code for i in range(6)]
    assert statuses == [200] * 5 + [429]


def test_only_citizens_file_and_only_officials_review(env):
    c = env["client"]
    assert c.post("/api/grievances", headers=env["shop"], json=COMPLAINT).status_code == 403
    assert c.post("/api/grievances", json=COMPLAINT).status_code == 401
    assert c.get("/api/grievances", headers=env["citizen"]).status_code == 403
    assert c.get("/api/grievances", headers=env["shop"]).status_code == 403
    assert c.get("/api/grievances/mine", headers=env["official"]).status_code == 403


def test_an_official_reviews_and_the_citizen_is_told(env):
    c = env["client"]
    g = file(env).json()["data"]
    listed = c.get("/api/grievances?status=Submitted", headers=env["official"]).json()["data"]
    assert [x["id"] for x in listed] == [g["id"]]

    r = c.post(f"/api/grievances/{g['id']}/status", headers=env["official"],
               json={"status": "Resolved", "note": "Shop gave the missing 1 kg wheat."})
    assert r.status_code == 200 and r.json()["data"]["status"] == "Resolved"
    mine = c.get("/api/grievances/mine", headers=env["citizen"]).json()["data"][0]
    assert (mine["status"], mine["resolutionNote"]) == ("Resolved", "Shop gave the missing 1 kg wheat.")
    notes = c.get("/api/notifications", headers=env["citizen"]).json()["data"]
    assert any("is now resolved" in n["message"] for n in notes)

    assert c.post(f"/api/grievances/{g['id']}/status", headers=env["official"], json={"status": "Submitted"}).status_code == 400
    assert c.post("/api/grievances/9999/status", headers=env["official"], json={"status": "Resolved"}).status_code == 404
    with session() as db:
        assert db.get(Grievance, g["id"]).Status == GrievanceStatus.Resolved
