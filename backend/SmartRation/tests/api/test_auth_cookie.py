"""Cookie mode for the website (S7): the refresh token lives only in an HttpOnly, SameSite=Strict cookie and never
appears in a response body; body mode (the Android app) is unchanged."""

from __future__ import annotations

import bcrypt
import pytest
from sqlalchemy import func, select

from app.database.base import Base
from app.database.connection import get_engine, get_session_factory
from app.database.models import RefreshToken, User
from app.utils.time import utc_now

COOKIE = {"X-Auth-Mode": "cookie"}
HASH = bcrypt.hashpw(b"demo123", bcrypt.gensalt(rounds=4)).decode()


@pytest.fixture
def api(make_client):
    client = make_client(lambda r: None)
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        db.add(User(Id=1, FullName="Rahul Patil", Email="rural@example.com", MobileNumber="9000000001", PasswordHash=HASH,
                    Role=1, IsActive=True, CreatedAt=utc_now()))
        db.commit()
    return client


def login(api, headers=COOKIE):
    return api.post("/api/v1/auth/login", headers=headers, json={"email": "rural@example.com", "password": "demo123"})


def set_cookie_header(response) -> str:
    return next(v for k, v in response.headers.multi_items() if k == "set-cookie" and v.startswith("sr_refresh="))


def active_sessions():
    with get_session_factory()() as db:
        return db.scalar(select(func.count()).select_from(RefreshToken).where(RefreshToken.RevokedAt.is_(None)))


def test_cookie_mode_keeps_the_refresh_token_out_of_the_body(api):
    r = login(api)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["refreshToken"] is None and data["accessToken"]
    header = set_cookie_header(r).lower()
    assert "httponly" in header and "samesite=strict" in header and "path=/api" in header and "max-age=604800" in header
    assert "secure" not in header                       # plain-http development; production and https add Secure
    assert api.cookies.get("sr_refresh")


def test_refresh_and_logout_use_the_cookie_and_the_body_never_carries_it(api):
    login(api)
    first = api.cookies.get("sr_refresh")
    r = api.post("/api/v1/auth/refresh", headers=COOKIE, json={})
    assert r.status_code == 200 and r.json()["data"]["refreshToken"] is None
    assert api.cookies.get("sr_refresh") != first       # rotated
    out = api.post("/api/v1/auth/logout", headers=COOKIE, json={})
    assert out.status_code == 200 and "max-age=0" in set_cookie_header(out).lower()   # cookie removed
    assert active_sessions() == 0


def test_without_the_header_the_cookie_is_ignored(api):
    login(api)                                          # the client now holds the cookie ...
    r = api.post("/api/v1/auth/refresh", json={})       # ... but a request without X-Auth-Mode (e.g. a cross-site form)
    assert r.status_code == 400                         # is body mode: the body has no token, nothing is refreshed


def test_a_dead_cookie_is_cleared(api):
    login(api)
    api.cookies.set("sr_refresh", "never-issued", path="/api")
    r = api.post("/api/v1/auth/refresh", headers=COOKIE, json={})
    assert r.status_code == 401 and "max-age=0" in set_cookie_header(r).lower()


def test_secure_flag_in_production(make_client, tmp_path):
    client = make_client(lambda r: None, environment="production", demo_otp_enabled=False, sms_allow_mock_outside_development=True)
    Base.metadata.create_all(get_engine())
    with get_session_factory()() as db:
        db.add(User(Id=1, FullName="Rahul Patil", Email="rural@example.com", MobileNumber="9000000001", PasswordHash=HASH,
                    Role=1, IsActive=True, CreatedAt=utc_now()))
        db.commit()
    assert "; secure" in set_cookie_header(login(client)).lower()


def test_body_mode_is_unchanged_for_the_app(api):
    r = login(api, headers={})
    data = r.json()["data"]
    assert len(data["refreshToken"]) == 88 and "sr_refresh" not in r.headers.get("set-cookie", "")
    assert api.post("/api/v1/auth/refresh", json={"refreshToken": data["refreshToken"]}).json()["data"]["refreshToken"]


def test_cors_lets_allowed_origins_send_the_mode_header_only(api):
    allowed = api.options("/api/v1/auth/refresh", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
                                                           "Access-Control-Request-Headers": "x-auth-mode,content-type"})
    assert allowed.status_code == 200 and "x-auth-mode" in allowed.headers["access-control-allow-headers"].lower()
    other = api.options("/api/v1/auth/refresh", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST",
                                                         "Access-Control-Request-Headers": "x-auth-mode"})
    assert other.status_code == 400 and "access-control-allow-origin" not in other.headers
    assert "access-control-allow-credentials" not in allowed.headers   # no cross-origin cookies at all
