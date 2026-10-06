"""Security events (Phase 10): permission refusals, rate-limit hits and oversized bodies are logged as structured
warnings with who and where — never the body, query string or token."""

from __future__ import annotations

import json
import logging

from sqlalchemy import select

from app.database.connection import get_session_factory
from app.database.models import Beneficiary, User


def events(caplog) -> list[dict]:
    return [r.fields for r in caplog.records if r.name == "smartration.security"]


def test_a_refused_record_is_logged_with_who_and_where(env, caplog):
    with get_session_factory()() as db:
        b = db.scalar(select(Beneficiary.Id).join(User, User.Id == Beneficiary.UserId).where(User.Email == "asha@example.com"))
    caplog.set_level(logging.WARNING, logger="smartration.security")
    r = env["client"].get(f"/api/beneficiaries/{b}/full-profile?secret=x", headers=env["other_shop"])
    assert r.status_code == 403
    (event,) = events(caplog)
    assert event["event"] == "permission_denied" and event["status"] == 403
    assert event["path"] == f"/api/beneficiaries/{b}/full-profile" and event["user_id"] == 51 and event["role"] == "ShopOwner"
    text = " ".join(str(v) for v in event.values())
    assert "secret" not in text and "Bearer" not in text


def test_rate_limit_hits_are_logged(env, caplog):
    caplog.set_level(logging.WARNING, logger="smartration.security")
    for _ in range(31):
        env["client"].get("/api/public/beneficiaries/NO-SUCH-CODE")
    assert [e["event"] for e in events(caplog)] == ["rate_limited"]
    assert events(caplog)[0]["path"] == "/api/public/beneficiaries/NO-SUCH-CODE"


def test_oversized_bodies_are_logged_without_the_body(make_client, capsys):
    api = make_client(lambda r: None)          # max_request_bytes=1024 in tests; JSON log lines go to stdout
    r = api.post("/api/chatbot/message", content=b'{"message":"' + b"z" * 2000 + b'"}', headers={"Content-Type": "application/json"})
    assert r.status_code == 413
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if '"smartration.security"' in line]
    assert [e["event"] for e in lines] == ["payload_too_large"]
    assert "zzzz" not in json.dumps(lines)
