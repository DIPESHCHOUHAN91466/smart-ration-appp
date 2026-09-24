"""Response envelope and exception handlers.

The shape matches the C# API exactly, because the frontend already depends on it:
    success -> {"success": true,  "message": "...", "data": ..., "errors": null}
    failure -> {"success": false, "message": "...", "data": null, "errors": [...]|null, "errorCode": "..."}
(`errorCode` is omitted when there is none, like the C# ApiResponse.)
Stack traces, SQL, paths and secrets never reach the client.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("smartration.errors")


def ok(data: Any = None, message: str = "Success") -> dict:
    return {"success": True, "message": message, "data": data, "errors": None}


def fail_body(message: str, errors: list[str] | None = None, error_code: str | None = None) -> dict:
    body = {"success": False, "message": message, "data": None, "errors": errors}
    if error_code:
        body["errorCode"] = error_code
    return body


class ApiError(Exception):
    """Expected failure with an HTTP status and a stable machine-readable code
    (mirrors the C# ApiException family)."""

    status_code = 400

    def __init__(self, message: str, error_code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code


class BadRequest(ApiError):
    status_code = 400


class Unauthorized(ApiError):
    status_code = 401


class Forbidden(ApiError):
    status_code = 403


class NotFound(ApiError):
    status_code = 404


class Conflict(ApiError):
    status_code = 409


class ServiceUnavailable(ApiError):
    status_code = 503


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError):
        errors = getattr(exc, "errors", None)  # ValidationFailed carries the "Field: message" list
        return JSONResponse(status_code=exc.status_code, content=fail_body(exc.message, errors, exc.error_code))

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError):
        # Field names and reasons only — never echo the submitted values.
        errors = [f"{'.'.join(str(p) for p in e['loc'][1:]) or 'body'}: {e['msg']}" for e in exc.errors()]
        # Same shape as the C# InvalidModelStateResponseFactory (no errorCode).
        return JSONResponse(status_code=400, content=fail_body("One or more validation errors occurred.", errors))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(_: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(status_code=exc.status_code, content=fail_body(message), headers=getattr(exc, "headers", None))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        log.exception("Unhandled error", extra={"fields": {"path": request.url.path}})
        return JSONResponse(status_code=500, content=fail_body("An unexpected error occurred. Please try again later.", error_code="INTERNAL_ERROR"))
