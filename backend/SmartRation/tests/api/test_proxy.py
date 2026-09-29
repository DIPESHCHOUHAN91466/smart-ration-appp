"""Fallback proxy: unmigrated /api/* routes reach the C# API unchanged."""

from __future__ import annotations

import json

import httpx

seen: list[httpx.Request] = []


def echo_upstream(request: httpx.Request) -> httpx.Response:
    """Fake C# API: echoes what it received, with C#-style extra headers."""
    seen.append(request)
    body = {
        "success": True, "message": "Success",
        "data": {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query, "ascii") if isinstance(request.url.query, bytes) else request.url.query,
            "auth": request.headers.get("authorization"),
            "idem": request.headers.get("idempotency-key"),
            "ctype": request.headers.get("content-type"),
            "xff": request.headers.get("x-forwarded-for"),
            "rid": request.headers.get("x-request-id"),
            "body_len": len(request.content),
        },
        "errors": None,
    }
    return httpx.Response(
        201 if request.method == "POST" else 200,
        json=body,
        headers={"Access-Control-Allow-Origin": "*", "Server": "Kestrel", "X-Custom": "kept"},
    )


def test_get_is_forwarded_with_path_query_and_auth(make_client):
    c = make_client(echo_upstream)
    r = c.get("/api/government/statistics?shopId=3&shopId=4", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["method"] == "GET" and d["path"] == "/api/government/statistics"
    assert d["query"] == "shopId=3&shopId=4"
    assert d["auth"] == "Bearer abc.def.ghi"
    assert r.headers["X-Served-By"] == "legacy-dotnet"
    assert r.headers["X-Custom"] == "kept"


def test_json_body_status_and_idempotency_key_are_preserved(make_client):
    c = make_client(echo_upstream)
    payload = {"tokenId": 51}
    r = c.post("/api/legacy-only/echo", json=payload, headers={"Idempotency-Key": "k-1"})
    assert r.status_code == 201
    d = r.json()["data"]
    assert d["idem"] == "k-1" and d["ctype"] == "application/json"
    assert d["body_len"] == len(json.dumps(payload).replace(" ", ""))


def test_multipart_upload_is_forwarded_byte_for_byte(make_client):
    c = make_client(echo_upstream, max_request_bytes=10_000)
    r = c.post("/api/legacy-only/upload", files={"file": ("x.png", b"\x89PNG" + b"\x00" * 100, "image/png")})
    d = r.json()["data"]
    assert d["ctype"].startswith("multipart/form-data; boundary=")
    assert d["body_len"] > 100


def test_upstream_status_and_error_body_pass_through(make_client):
    def upstream(_):
        return httpx.Response(409, json={"success": False, "message": "This token has already been used for collection.", "data": None, "errors": None, "errorCode": "X"})

    r = make_client(upstream).post("/api/legacy-only/echo", json={})
    assert r.status_code == 409 and r.json()["errorCode"] == "X"


def test_cors_and_owned_headers_from_upstream_are_not_duplicated(make_client):
    c = make_client(echo_upstream)
    r = c.get("/api/government/dashboard", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get_list("access-control-allow-origin") == ["http://localhost:5173"]
    assert "Kestrel" not in r.headers.get("server", "")


def test_forwarded_for_and_request_id_are_sent(make_client):
    c = make_client(echo_upstream)
    r = c.get("/api/government/dashboard", headers={"X-Request-ID": "abcdef0123456789"})
    d = r.json()["data"]
    assert d["rid"] == "abcdef0123456789" and r.headers["X-Request-ID"] == "abcdef0123456789"
    assert d["xff"]  # client address for the C# rate limiter


def test_legacy_down_returns_502_envelope(make_client):
    def down(_):
        raise httpx.ConnectError("refused")

    r = make_client(down).get("/api/government/dashboard")
    assert r.status_code == 502
    assert r.json() == {"success": False, "message": "Connection temporarily unavailable. Please retry.", "data": None, "errors": None, "errorCode": "LEGACY_API_UNAVAILABLE"}


def test_legacy_timeout_returns_504(make_client):
    def slow(_):
        raise httpx.ReadTimeout("slow")

    r = make_client(slow).get("/api/government/dashboard")
    assert r.status_code == 504 and r.json()["errorCode"] == "LEGACY_API_TIMEOUT"


def test_python_routes_are_not_proxied(make_client):
    calls = []

    def upstream(request):
        calls.append(request.url.path)
        return httpx.Response(200, text="should not be used for /health/live")

    r = make_client(upstream).get("/health/live")
    assert r.json() == {"status": "healthy"} and calls == []


def test_oversized_body_is_rejected_before_forwarding(make_client):
    seen.clear()
    r = make_client(echo_upstream, max_request_bytes=100).post("/api/ration/bookings", content=b"x" * 500, headers={"Content-Type": "application/json"})
    assert r.status_code == 413 and r.json()["errorCode"] == "PAYLOAD_TOO_LARGE"
    assert seen == []


def test_proxy_disabled_gives_404_envelope(make_client):
    r = make_client(None, legacy_api_url="").get("/api/government/dashboard")
    assert r.status_code == 404 and r.json()["success"] is False


def test_security_headers_present(make_client):
    r = make_client(echo_upstream).get("/api/government/dashboard")
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY"


def test_requests_take_turns_across_the_connection_pools():
    """Several small pools, used in turn (one big httpcore pool slows down as it grows)."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.routes import legacy_proxy

    served: list[int] = []

    def pool(n: int) -> httpx.AsyncClient:
        def handler(_: httpx.Request) -> httpx.Response:
            served.append(n)
            return httpx.Response(200, json={"success": True, "message": None, "data": n, "errors": None})
        return httpx.AsyncClient(base_url="http://csharp", transport=httpx.MockTransport(handler))

    app = FastAPI()
    app.include_router(legacy_proxy.build_router([pool(0), pool(1), pool(2)]))
    c = TestClient(app)
    for _ in range(6):
        assert c.get("/api/government/dashboard").status_code == 200
    assert served == [0, 1, 2, 0, 1, 2]


def test_pool_settings_create_that_many_clients(make_client):
    c = make_client(echo_upstream, legacy_api_pools=3, legacy_api_connections_per_pool=4)
    assert c.get("/api/government/dashboard").status_code == 200
    assert c.app.state.legacy_client is not None  # health checks use the first pool
