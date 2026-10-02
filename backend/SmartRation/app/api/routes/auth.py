"""/api/auth — migrated from the C# AuthController (same routes, bodies, statuses)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.errors import ok
from app.core.validation import ValidationFailed, validate
from app.database.connection import get_db
from app.schemas.auth import (
    LOGIN_RULES,
    OTP_REQUEST_RULES,
    OTP_VERIFY_RULES,
    REFRESH_RULES,
    REGISTER_RULES,
    AuthEnvelope,
    EmptyEnvelope,
    LoginRequest,
    OtpLoginRequest,
    OtpLoginVerify,
    OtpSentEnvelope,
    RefreshRequest,
    RegisterRequest,
)
from app.security.rate_limit import rate_limit
from app.services import auth_service, login_otp_service
from app.services.auth_service import RequestContext

router = APIRouter(prefix="/api/auth", tags=["auth"])

auth_limit = Depends(rate_limit("auth", lambda s: s.auth_rate_limit_per_minute))
otp_limit = Depends(rate_limit("otp", lambda s: s.otp_rate_limit_per_minute))

ERRORS = {
    400: {"description": "Validation failed: `errors` lists \"Field: message\" items"},
    401: {"description": "Invalid credentials / refresh token"},
    409: {"description": "Email or mobile number already registered"},
    429: {"description": "Too many attempts from this address (10/min)"},
}


async def _json(request: Request) -> dict | None:
    try:
        return json.loads(await request.body() or b"null")
    except ValueError:
        raise ValidationFailed(["$: The request body is not valid JSON."]) from None


def _ctx(request: Request) -> RequestContext:
    return RequestContext(ip_address=request.client.host if request.client else None)


@router.post("/register", summary="Register a Rural User account", response_model=AuthEnvelope,
             dependencies=[auth_limit], responses={k: ERRORS[k] for k in (400, 409, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": RegisterRequest.model_json_schema()}}, "required": True}})
async def register(request: Request, db: Session = Depends(get_db)):
    body = await _json(request)
    v = validate(body, REGISTER_RULES)
    # Optional, so older clients keep working; the website requires it (DPDP: consent is recorded in the audit log).
    consent = isinstance(body, dict) and any(k.lower() == "consenttoprivacypolicy" and val is True for k, val in body.items())
    # Blocking DB work and Argon2 hashing run off the event loop.
    data = await run_in_threadpool(auth_service.register, db, request.app.state.settings, _ctx(request),
                                   v["FullName"], v["Email"], v["MobileNumber"], v["Password"], consent)
    return ok(data, "Registration successful")


@router.post("/login", summary="Log in with email and password", response_model=AuthEnvelope,
             dependencies=[auth_limit], responses={k: ERRORS[k] for k in (400, 401, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": LoginRequest.model_json_schema()}}, "required": True}})
async def login(request: Request, db: Session = Depends(get_db)):
    v = validate(await _json(request), LOGIN_RULES)
    data = await run_in_threadpool(auth_service.login, db, request.app.state.settings, _ctx(request), v["Email"], v["Password"])
    return ok(data, "Login successful")


@router.post("/refresh", summary="Exchange a refresh token for new tokens (rotates it)", response_model=AuthEnvelope,
             responses={k: ERRORS[k] for k in (400, 401)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": RefreshRequest.model_json_schema()}}, "required": True}})
async def refresh(request: Request, db: Session = Depends(get_db)):
    v = validate(await _json(request), REFRESH_RULES)
    return ok(await run_in_threadpool(auth_service.refresh, db, request.app.state.settings, v["RefreshToken"]), "Token refreshed")


@router.post("/otp/request", summary="Send a sign-in code to a citizen's registered mobile", response_model=OtpSentEnvelope,
             dependencies=[otp_limit],
             responses={400: ERRORS[400], 429: ERRORS[429], 503: {"description": "The SMS could not be sent"}},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": OtpLoginRequest.model_json_schema()}}, "required": True}})
async def otp_request(request: Request, db: Session = Depends(get_db)):
    v = validate(await _json(request), OTP_REQUEST_RULES)
    data = await run_in_threadpool(login_otp_service.request_code, db, request.app.state.settings, _ctx(request), v["MobileNumber"])
    # The same answer whether or not the number is registered (no account probing).
    return ok(data, "If this number is registered, a code has been sent.")


@router.post("/otp/verify", summary="Sign in with the code (Rural Users)", response_model=AuthEnvelope,
             dependencies=[auth_limit, otp_limit], responses={k: ERRORS[k] for k in (400, 401, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": OtpLoginVerify.model_json_schema()}}, "required": True}})
async def otp_verify(request: Request, db: Session = Depends(get_db)):
    v = validate(await _json(request), OTP_VERIFY_RULES)
    data = await run_in_threadpool(login_otp_service.verify_code, db, request.app.state.settings, _ctx(request),
                                   v["MobileNumber"], v["Otp"])
    return ok(data, "Login successful")


@router.post("/logout", summary="Revoke a refresh token", response_model=EmptyEnvelope, responses={400: ERRORS[400]},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": RefreshRequest.model_json_schema()}}, "required": True}})
async def logout(request: Request, db: Session = Depends(get_db)):
    v = validate(await _json(request), REFRESH_RULES)
    await run_in_threadpool(auth_service.logout, db, _ctx(request), v["RefreshToken"])
    return ok(None, "Logged out")

