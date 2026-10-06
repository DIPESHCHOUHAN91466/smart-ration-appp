"""Pure ASGI middleware at the edge of the app: who the client really is, and how much it may send.

ClientAddressMiddleware (security N1)
    Behind a reverse proxy the socket address is the proxy's, and the X-Forwarded-For header is a list the CLIENT
    starts and every proxy appends to. Only the entries added by our own proxies can be trusted, so the client
    address is read `TRUSTED_PROXY_HOPS` entries from the right:
        0 (default)  no proxy: ignore the header, use the socket address
        1            one proxy that appends the peer address (nginx `$proxy_add_x_forwarded_for`)
        2            Render: its edge appends the client, then its proxy appends itself
    The left-most entry (what uvicorn's `--forwarded-allow-ips "*"` used) is whatever the client typed, so it
    could defeat every per-IP rate limit and forge the IPs in the audit log. X-Forwarded-Proto is honoured only
    when proxies are trusted. Run uvicorn with --no-proxy-headers so it does not rewrite the address first.

BodySizeLimitMiddleware (security N5)
    The limit used to be checked only against Content-Length; a chunked body has none, and was read whole however
    large. Every body is now read up to MAX_REQUEST_BYTES and refused with 413 as soon as it passes the limit, then
    replayed to the application (which read bodies whole anyway, so memory use does not grow).
"""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import fail_body, log_security_event


def _header(scope: Scope, name: bytes) -> str | None:
    values = [v.decode("latin-1") for k, v in scope.get("headers", []) if k == name]
    return ",".join(values) if values else None


class ClientAddressMiddleware:
    def __init__(self, app: ASGIApp, trusted_hops: int) -> None:
        self.app = app
        self.hops = trusted_hops

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket") and self.hops > 0:
            forwarded = _header(scope, b"x-forwarded-for")
            if forwarded:
                hosts = [h.strip() for h in forwarded.split(",") if h.strip()]
                if hosts:
                    # Fewer entries than hops: nothing was prepended by the client, the first one is the client.
                    host = hosts[-self.hops] if len(hosts) >= self.hops else hosts[0]
                    scope = {**scope, "client": (host[:64], 0)}
            proto = _header(scope, b"x-forwarded-proto")
            if proto:
                last = proto.split(",")[-1].strip().lower()
                if last in ("http", "https"):
                    scope = {**scope, "scheme": last if scope["type"] == "http" else last.replace("http", "ws")}
        await self.app(scope, receive, send)


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def _too_large(self, scope: Scope, receive: Receive, send: Send) -> None:
        log_security_event(Request(scope), 413, "PAYLOAD_TOO_LARGE")
        response = JSONResponse(status_code=413, content=fail_body("Request body is too large.", error_code="PAYLOAD_TOO_LARGE"))
        await response(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = _header(scope, b"content-length")
        if declared and declared.isdigit() and int(declared) > self.max_bytes:
            await self._too_large(scope, receive, send)
            return

        chunks: list[bytes] = []
        total = 0
        pending: Message | None = None
        while True:
            message = await receive()
            if message["type"] != "http.request":       # the client went away: the app sees it after the body
                pending = message
                break
            body = message.get("body", b"")
            total += len(body)
            if total > self.max_bytes:
                await self._too_large(scope, receive, send)
                return
            chunks.append(body)
            if not message.get("more_body", False):
                break

        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            if pending is not None:
                return pending
            return await receive()

        await self.app(scope, replay, send)
