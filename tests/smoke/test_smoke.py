"""Post-deployment smoke test: is the deployment up, connected, secured and answering real requests?"""

from __future__ import annotations

import pytest


def test_liveness(client):
    r = client.get("/health/live")
    assert r.status_code == 200


def test_health_reports_a_working_database(client):
    r = client.get("/health")
    body = r.json()
    assert r.status_code == 200, body
    assert body["status"] in ("healthy", "degraded") and body["database"] == "healthy"
    assert body["dataMode"] in ("synthetic", "real")


def test_ready_database_migrations_and_business_api(client):
    r = client.get("/ready")
    body = r.json()
    assert r.status_code == 200 and body["ready"] is True, body
    assert body["checks"]["database"] == "ok" and body["checks"]["migrations"] == "ok"


def test_health_never_reveals_connection_details(client):
    text = client.get("/health").text + client.get("/ready").text + client.get("/health/db").text
    for secret_shaped in ("mysql+pymysql", "password", "@localhost", "ssl_ca"):
        assert secret_shaped not in text.lower()


def test_public_help_is_served_from_the_database_and_knowledge_base(client):
    r = client.get("/api/v1/public-help/categories", params={"language": "en"})
    assert r.status_code == 200 and r.json()["success"] is True
    assert r.json()["data"], "no Public Help categories"


def test_the_chatbot_answers(client):
    r = client.post("/api/v1/chatbot/message", json={"message": "How do I book a ration slot?", "language": "en"})
    assert r.status_code == 200, r.text
    reply = r.json()["data"]
    assert reply["text"] and reply["kind"] != "error"


def test_business_routes_require_sign_in(client):
    r = client.get("/api/v1/tokens/today")  # proxied to the C# API; shop owners only
    assert r.status_code == 401 and r.json()["success"] is False


def test_security_headers(client):
    headers = client.get("/health/live").headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-request-id")


def test_the_website_is_served_when_bundled(client):
    r = client.get("/")
    if r.status_code == 404:
        pytest.skip("this deployment serves the API only (the website is served elsewhere)")
    assert r.status_code == 200 and '<div id="root">' in r.text
    assert client.get("/rural/dashboard").status_code == 200  # client-side routes survive a reload


def test_https_redirect_or_local(base_url, client):
    if base_url.startswith("http://") and not base_url.startswith(("http://127.0.0.1", "http://localhost")):
        pytest.fail("a public deployment must be served over HTTPS")
