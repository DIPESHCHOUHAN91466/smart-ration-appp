"""Security controls of the Python gateway: authentication, role checks, hostile input, error hygiene,
CORS and log hygiene. Each test states the attack it covers."""

from __future__ import annotations

import logging
from datetime import timedelta

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from py_testkit import make_settings
from sqlalchemy import func, select

from app.api.dependencies.auth import CurrentUser, require_roles
from app.core.errors import install_exception_handlers
from app.database.base import Base
from app.database.session import get_engine, get_session_factory
from app.models import User
from app.models.enums import UserRole
from app.security.passwords import hash_password
from app.security.tokens import ROLE_CLAIM, TokenUser, create_access_token
from app.utils.time import utc_now

PASSWORD = "Str0ng-test-passphrase"


@pytest.fixture
def guarded(tmp_path):
    """A tiny app with one route that only government officials may call."""
    settings = make_settings(tmp_path)
    app = FastAPI()
    app.state.settings = settings
    install_exception_handlers(app)

    @app.get("/official-only")
    def official_only(user: CurrentUser = Depends(require_roles(UserRole.GovernmentOfficial))):
        return {"user": user.user_id}

    return TestClient(app), settings


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def token_for(settings, role: str, **changes) -> str:
    token, _ = create_access_token(TokenUser(5, "x@example.com", "X", role, None), settings)
    if not changes:
        return token
    claims = jwt.decode(token, options={"verify_signature": False})
    claims.update(changes)
    return jwt.encode(claims, settings.jwt_secret_key, algorithm="HS256")


# ------------------------------------------------------------------ authentication and authorization

def test_missing_or_malformed_authorization_is_401(guarded):
    client, _ = guarded
    for headers in ({}, {"Authorization": "Bearer"}, {"Authorization": "Basic dXNlcjpwYXNz"}, {"Authorization": "Bearer not.a.jwt"}):
        r = client.get("/official-only", headers=headers)
        assert r.status_code == 401 and r.json()["success"] is False


def test_expired_token_is_401(guarded):
    client, settings = guarded
    expired = token_for(settings, "GovernmentOfficial", exp=int((utc_now() - timedelta(hours=1)).timestamp()))
    assert client.get("/official-only", headers=bearer(expired)).status_code == 401


def test_token_signed_with_another_key_is_401(guarded, tmp_path):
    client, _ = guarded
    other = make_settings(tmp_path, jwt_secret_key="attacker-controlled-key-0123456789abcdef-0123")
    assert client.get("/official-only", headers=bearer(token_for(other, "GovernmentOfficial"))).status_code == 401


def test_alg_none_token_is_401(guarded):
    client, settings = guarded
    claims = jwt.decode(token_for(settings, "GovernmentOfficial"), options={"verify_signature": False})
    unsigned = jwt.encode(claims, key="", algorithm="none")
    assert client.get("/official-only", headers=bearer(unsigned)).status_code == 401


def test_wrong_issuer_or_audience_is_401(guarded):
    client, settings = guarded
    for change in ({"iss": "someone-else"}, {"aud": "another-app"}):
        assert client.get("/official-only", headers=bearer(token_for(settings, "GovernmentOfficial", **change))).status_code == 401


def test_unknown_role_claim_is_401_not_a_crash(guarded):
    client, settings = guarded
    r = client.get("/official-only", headers=bearer(token_for(settings, "GovernmentOfficial", **{ROLE_CLAIM: "SuperAdmin"})))
    assert r.status_code == 401


@pytest.mark.parametrize("role", ["RuralUser", "ShopOwner"])
def test_other_roles_are_403(guarded, role):
    client, settings = guarded
    r = client.get("/official-only", headers=bearer(token_for(settings, role)))
    assert r.status_code == 403 and r.json()["message"] == "You do not have permission to perform this action."


def test_the_right_role_is_allowed(guarded):
    client, settings = guarded
    r = client.get("/official-only", headers=bearer(token_for(settings, "GovernmentOfficial")))
    assert r.status_code == 200 and r.json() == {"user": 5}


# ------------------------------------------------------------------ hostile input through the real app

@pytest.fixture
def api(make_client):
    client = make_client(lambda r: None)
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        db.add(User(Id=1, FullName="Rahul", Email="rural@example.com", MobileNumber="9000000001", PasswordHash=hash_password(PASSWORD),
                    Role=1, IsActive=True, CreatedAt=utc_now()))
        db.commit()
    return client


@pytest.mark.parametrize("email", ["' OR '1'='1", "rural@example.com' --", "rural@example.com\" OR \"\"=\"", "admin'/*"])
def test_sql_injection_in_login_never_signs_in(api, email):
    r = api.post("/api/auth/login", json={"email": email, "password": "' OR '1'='1"})
    assert r.status_code in (400, 401) and r.json()["data"] is None
    with get_session_factory()() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1


def test_unexpected_errors_hide_internal_details(make_client):
    client = make_client(lambda r: None)

    @client.app.get("/api/boom")
    def boom():
        raise RuntimeError("password=hunter2 at C:\\secret\\path.py line 42")

    r = client.get("/api/boom")
    assert r.status_code == 500
    text = r.text
    assert "hunter2" not in text and "secret" not in text and "Traceback" not in text and "RuntimeError" not in text
    assert r.json()["success"] is False


def test_cors_does_not_allow_unknown_origins(make_client):
    client = make_client(lambda r: None)
    r = client.options("/api/auth/login", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") != "https://evil.example"
    ok = client.options("/api/auth/login", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_forged_request_ids_are_replaced(make_client):
    client = make_client(lambda r: None)
    r = client.get("/health/live", headers={"X-Request-ID": "<script>alert(1)</script>"})
    assert "<" not in r.headers["X-Request-ID"]


def test_passwords_and_tokens_never_reach_the_logs(api, caplog):
    caplog.set_level(logging.DEBUG)
    r = api.post("/api/auth/login", json={"email": "rural@example.com", "password": PASSWORD})
    assert r.status_code == 200
    api.post("/api/auth/login", json={"email": "rural@example.com", "password": PASSWORD + "-wrong"})
    logged = "\n".join(f"{rec.getMessage()} {getattr(rec, 'fields', '')}" for rec in caplog.records)
    assert PASSWORD not in logged
    assert r.json()["data"]["accessToken"] not in logged and r.json()["data"]["refreshToken"] not in logged
