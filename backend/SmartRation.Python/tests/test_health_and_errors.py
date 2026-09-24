from __future__ import annotations

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import Conflict, install_exception_handlers


def healthy_legacy(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200 if request.url.path == "/health" else 404, json={})


def test_health_reports_database_and_legacy(make_client):
    r = make_client(healthy_legacy).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy", "database": "healthy", "legacyApi": "healthy"}


def test_health_degraded_when_legacy_down(make_client):
    def down(_):
        raise httpx.ConnectError("refused")

    assert make_client(down).get("/health").json()["status"] == "degraded"


def test_health_unhealthy_503_when_database_down(make_client, tmp_path):
    bad = f"sqlite:///{(tmp_path / 'missing' / 'x.db').as_posix()}"
    r = make_client(healthy_legacy, database_url=bad).get("/health")
    assert r.status_code == 503 and r.json()["database"] == "unhealthy"


def test_docs_and_openapi_available(make_client):
    c = make_client(healthy_legacy)
    assert c.get("/docs").status_code == 200 and c.get("/redoc").status_code == 200
    assert "/health" in c.get("/openapi.json").json()["paths"]


def _app_with_routes() -> TestClient:
    app = FastAPI()
    install_exception_handlers(app)

    class Body(BaseModel):
        tokenId: int

    @app.post("/validate")
    def validate(body: Body):
        return {}

    @app.get("/conflict")
    def conflict():
        raise Conflict("Already collected.", "ALREADY_COLLECTED")

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret connection string and C:\\internal\\path")

    return TestClient(app, raise_server_exceptions=False)


def test_error_envelopes_match_the_csharp_api():
    c = _app_with_routes()
    r = c.get("/conflict")
    assert r.status_code == 409
    assert r.json() == {"success": False, "message": "Already collected.", "data": None, "errors": None, "errorCode": "ALREADY_COLLECTED"}

    r = c.post("/validate", json={"tokenId": "not-a-number"})
    assert r.status_code == 400 and "errorCode" not in r.json()  # C# validation responses carry none
    assert "not-a-number" not in r.text  # submitted values are never echoed

    r = c.get("/boom")
    assert r.status_code == 500 and "secret" not in r.text and "internal" not in r.text


def _migrate(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    from app.db.database import MIGRATIONS_DIR

    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.attributes["database_url"] = url  # never fall back to the .env (live) database
    command.upgrade(cfg, "head")


def test_ready_when_database_migrated_and_legacy_up(make_client, tmp_path):
    url = f"sqlite:///{(tmp_path / 'unit.db').as_posix()}"
    _migrate(url)
    r = make_client(healthy_legacy).get("/ready")
    assert r.status_code == 200
    assert r.json() == {"ready": True, "checks": {"database": "ok", "migrations": "ok", "legacyApi": "ok"}}


def test_not_ready_when_schema_not_migrated(make_client):
    r = make_client(healthy_legacy).get("/ready")
    assert r.status_code == 503
    body = r.json()
    assert body["ready"] is False and body["checks"]["migrations"].startswith("failing")


def test_not_ready_when_legacy_down(make_client, tmp_path):
    url = f"sqlite:///{(tmp_path / 'unit.db').as_posix()}"
    _migrate(url)

    def down(request):
        raise httpx.ConnectError("refused")

    r = make_client(down).get("/ready")
    assert r.status_code == 503 and r.json()["checks"]["legacyApi"] == "failing"
