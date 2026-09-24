"""Fallback proxy: forwards every /api/* route that is NOT yet implemented in
Python to the C# API, unchanged.

This is the compatibility layer for the side-by-side migration. The frontend
can talk only to FastAPI while the C# API keeps serving whatever hasn't been
migrated. It must be registered LAST so real Python routes always win.

Forwarded: method, path, query string, body (JSON or multipart, streamed
as-is), Authorization and other end-to-end headers, plus X-Forwarded-For /
X-Request-ID. Hop-by-hop headers are dropped both ways. The response status,
body and headers come back unchanged, marked `X-Served-By: legacy-dotnet`.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from app.core.errors import fail_body
from app.core.logging import request_id_var

log = logging.getLogger("smartration.proxy")

# RFC 7230 hop-by-hop headers + ones httpx/uvicorn recompute themselves.
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer",
    "transfer-encoding", "upgrade", "host", "content-length", "content-encoding",
}

# Response headers FastAPI/uvicorn set themselves; forwarding the upstream's
# copies would duplicate them (duplicate Access-Control-Allow-Origin makes
# browsers reject the response).
RESPONSE_OWNED = {"date", "server"}

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


def build_router(client: httpx.AsyncClient) -> APIRouter:
    router = APIRouter(include_in_schema=False)

    @router.api_route("/api/{path:path}", methods=METHODS)
    async def forward(path: str, request: Request) -> Response:
        # x-forwarded-for / x-request-id are rebuilt below (never duplicated).
        headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP | {"x-forwarded-for", "x-request-id"}}
        client_ip = request.client.host if request.client else ""
        prior = request.headers.get("x-forwarded-for")
        headers["X-Forwarded-For"] = f"{prior}, {client_ip}" if prior else client_ip
        headers["X-Request-ID"] = request_id_var.get()

        upstream = client.build_request(
            request.method,
            f"/api/{path}",
            params=request.query_params.multi_items(),
            headers=headers,
            content=await request.body(),
        )
        try:
            reply = await client.send(upstream)
        except httpx.TimeoutException:
            log.warning("legacy API timeout", extra={"fields": {"path": f"/api/{path}"}})
            return JSONResponse(status_code=504, content=fail_body("The service took too long to respond. Please retry.", error_code="LEGACY_API_TIMEOUT"))
        except httpx.HTTPError as exc:
            log.warning("legacy API unreachable", extra={"fields": {"path": f"/api/{path}", "error": type(exc).__name__}})
            return JSONResponse(status_code=502, content=fail_body("Connection temporarily unavailable. Please retry.", error_code="LEGACY_API_UNAVAILABLE"))

        out_headers = {
            k: v for k, v in reply.headers.items()
            if k.lower() not in HOP_BY_HOP and k.lower() not in RESPONSE_OWNED and not k.lower().startswith("access-control-")
        }
        out_headers["X-Served-By"] = "legacy-dotnet"
        return Response(content=reply.content, status_code=reply.status_code, headers=out_headers)

    return router
