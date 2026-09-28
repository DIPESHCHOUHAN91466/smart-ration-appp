"""/api/v1/* is an alias of /api/*: Python routes and proxied C# routes answer under both."""

from __future__ import annotations

import httpx
import pytest

from app.middleware.api_version import strip_version

seen: list[str] = []


def upstream(request: httpx.Request) -> httpx.Response:
    seen.append(request.url.path)
    return httpx.Response(200, json={"success": True, "message": "Success", "data": {"path": request.url.path}, "errors": None})


@pytest.mark.parametrize(("path", "expected"), [
    ("/api/v1/shops", "/api/shops"),
    ("/api/v1", "/api"),
    ("/api/v1/", "/api/"),
    ("/api/shops", None),
    ("/api/v10/shops", None),
    ("/v1/api/shops", None),
    ("/rural/dashboard", None),
])
def test_strip_version(path, expected):
    assert strip_version(path) == expected


def test_proxied_route_reaches_csharp_without_the_version(make_client):
    c = make_client(upstream)
    r = c.get("/api/v1/ration/items?shopId=2", headers={"Authorization": "Bearer a.b.c"})
    assert r.status_code == 200
    assert r.json()["data"]["path"] == "/api/ration/items"  # C# only knows /api/*
    assert r.headers["X-Served-By"] == "legacy-dotnet"


def test_python_route_answers_under_both_prefixes(make_client):
    c = make_client(upstream)
    plain, versioned = c.get("/api/public-help/topics"), c.get("/api/v1/public-help/topics")
    assert plain.status_code == versioned.status_code == 200
    assert plain.json() == versioned.json()


def test_python_errors_are_identical_under_v1(make_client):
    c = make_client(upstream)
    plain = c.post("/api/auth/login", json={})
    versioned = c.post("/api/v1/auth/login", json={})
    assert plain.status_code == versioned.status_code == 400  # validation error envelope
    assert plain.json() == versioned.json()


def test_other_versions_are_not_rewritten(make_client):
    seen.clear()
    make_client(upstream).get("/api/v2/shops")
    assert seen == ["/api/v2/shops"]  # forwarded untouched (C# answers 404), never silently mapped to v1
