"""Request id, access logging, security headers and request-size limit."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import fail_body, unexpected_error_response
from app.core.logging import request_id_var

log = logging.getLogger("smartration.access")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-site",
}


def install_middleware(app: FastAPI, max_request_bytes: int) -> None:
    @app.middleware("http")
    async def request_context(request: Request, call_next):
        # Accept a caller's id only if it looks like one; otherwise make our own.
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if 8 <= len(incoming) <= 64 and incoming.replace("-", "").isalnum() else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            length = request.headers.get("content-length")
            if length and length.isdigit() and int(length) > max_request_bytes:
                response = JSONResponse(status_code=413, content=fail_body("Request body is too large.", error_code="PAYLOAD_TOO_LARGE"))
            else:
                try:
                    response = await call_next(request)
                except Exception as exc:  # unhandled: log with this request's id, answer with a clean 500
                    response = unexpected_error_response(request, exc)
            response.headers["X-Request-ID"] = request_id
            for name, value in SECURITY_HEADERS.items():
                response.headers.setdefault(name, value)
            log.info(
                "request",
                extra={"fields": {
                    "method": request.method,
                    "path": request.url.path,  # path only: query strings can carry personal data
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    "served_by": response.headers.get("X-Served-By", "python"),
                }},
            )
            return response
        finally:
            request_id_var.reset(token)
