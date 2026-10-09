"""Edge middleware: the real client address behind proxies (N1), the body limit for chunked bodies (N5), and the
rate limit on the public verification badge (N7)."""

from __future__ import annotations

import asyncio

import pytest

from app.database.base import Base
from app.database.connection import get_engine
from app.middleware.edge import BodySizeLimitMiddleware, ClientAddressMiddleware


def http_scope(headers=(), client=("10.0.0.9", 1234)):
    return {"type": "http", "method": "POST", "path": "/x", "headers": [(k.encode(), v.encode()) for k, v in headers],
            "client": client, "scheme": "http", "query_string": b""}


def capture(middleware_cls, scope, chunks=(b"",), **kwargs):
    seen: dict = {}
    sent: list = []
    messages = [{"type": "http.request", "body": c, "more_body": i < len(chunks) - 1} for i, c in enumerate(chunks)]

    async def inner(scope_, receive, send):
        seen["scope"] = scope_
        seen["body"] = (await receive()).get("body", b"")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    asyncio.run(middleware_cls(inner, **kwargs)(scope, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    return seen, status


# ---------------------------------------------------------------- client address (N1)

@pytest.mark.parametrize("hops, forwarded, expected", [
    (0, "6.6.6.6", "10.0.0.9"),                              # no proxy trusted: the header is ignored
    (1, "6.6.6.6, 203.0.113.7", "203.0.113.7"),              # nginx appended the real peer
    (2, "6.6.6.6, 203.0.113.7, 10.1.1.1", "203.0.113.7"),    # Render: client, then its proxy
    (2, "203.0.113.7, 10.1.1.1", "203.0.113.7"),             # nothing prepended by the client
    (2, "203.0.113.7", "203.0.113.7"),                       # fewer entries than hops: the only one
    (1, "6.6.6.6, 203.0.113.7:51234", "203.0.113.7"),        # Azure App Service: the port is dropped
    (1, "[2001:db8::1]:51234", "2001:db8::1"),               # Azure, IPv6 with a port
    (1, "2001:db8::1", "2001:db8::1"),                       # bare IPv6 is not mistaken for host:port
])
def test_the_client_address_is_counted_from_the_right(hops, forwarded, expected):
    seen, _ = capture(ClientAddressMiddleware, http_scope([("x-forwarded-for", forwarded)]), trusted_hops=hops)
    assert seen["scope"]["client"][0] == expected


def test_forwarded_proto_only_counts_behind_trusted_proxies():
    scope = http_scope([("x-forwarded-proto", "https")])
    assert capture(ClientAddressMiddleware, scope, trusted_hops=0)[0]["scope"]["scheme"] == "http"
    assert capture(ClientAddressMiddleware, scope, trusted_hops=1)[0]["scope"]["scheme"] == "https"


def test_rotating_a_fake_left_entry_no_longer_escapes_the_sign_in_limit(make_client):
    api = make_client(lambda r: None, trusted_proxy_hops=1)
    Base.metadata.create_all(get_engine())
    codes = [api.post("/api/auth/login", headers={"X-Forwarded-For": f"6.6.6.{i}, 203.0.113.7"},
                      json={"email": "x@y.z", "password": "bad"}).status_code for i in range(12)]
    assert codes[:10] == [401] * 10 and codes[10:] == [429, 429]                          # the same real client, whatever it claims first


def test_a_new_source_port_does_not_escape_the_sign_in_limit(make_client):
    api = make_client(lambda r: None, trusted_proxy_hops=1)
    Base.metadata.create_all(get_engine())
    codes = [api.post("/api/auth/login", headers={"X-Forwarded-For": f"203.0.113.7:{50000 + i}"},
                      json={"email": "x@y.z", "password": "bad"}).status_code for i in range(12)]
    assert codes[:10] == [401] * 10 and codes[10:] == [429, 429]   # Azure gives each connection a new port


def test_different_real_clients_keep_separate_limits(make_client):
    api = make_client(lambda r: None, trusted_proxy_hops=1)
    Base.metadata.create_all(get_engine())
    for _ in range(10):
        api.post("/api/auth/login", headers={"X-Forwarded-For": "203.0.113.7"}, json={"email": "x@y.z", "password": "bad"})
    other = api.post("/api/auth/login", headers={"X-Forwarded-For": "198.51.100.4"}, json={"email": "x@y.z", "password": "bad"})
    assert other.status_code == 401


# ---------------------------------------------------------------- body limit (N5)

def test_a_chunked_body_over_the_limit_is_refused_without_reaching_the_app():
    seen, status = capture(BodySizeLimitMiddleware, http_scope(), chunks=(b"a" * 600, b"a" * 600), max_bytes=1000)
    assert status == 413 and "scope" not in seen


def test_a_declared_length_over_the_limit_is_refused_before_reading():
    seen, status = capture(BodySizeLimitMiddleware, http_scope([("content-length", "5000")]), chunks=(b"x",), max_bytes=1000)
    assert status == 413 and "scope" not in seen


def test_a_chunked_body_within_the_limit_reaches_the_app_whole():
    seen, status = capture(BodySizeLimitMiddleware, http_scope(), chunks=(b"abc", b"def", b"ghi"), max_bytes=1000)
    assert status == 200 and seen["body"] == b"abcdefghi"


def test_the_api_refuses_a_large_chunked_body(make_client):
    api = make_client(lambda r: None)                       # make_settings: max_request_bytes=1024

    def chunks():
        for _ in range(4):
            yield b"a" * 600

    r = api.post("/api/chatbot/message", content=chunks(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413 and r.json()["errorCode"] == "PAYLOAD_TOO_LARGE"


# ---------------------------------------------------------------- public badge (N7)

def test_the_public_badge_is_rate_limited(env):
    codes = [env["client"].get("/api/public/beneficiaries/NO-SUCH-CODE").status_code for _ in range(31)]
    assert codes[:30] == [404] * 30 and codes[30] == 429
