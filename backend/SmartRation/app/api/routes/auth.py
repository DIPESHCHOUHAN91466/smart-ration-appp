"""/api/auth — migrated from the C# AuthController (same routes, bodies, statuses).

Two ways to hold the refresh token:
  * body mode (the Android app, API clients): it is returned in the JSON and sent back in the JSON, as before;
  * cookie mode (the website): requests carry `X-Auth-Mode: cookie`. The refresh token then lives only in an
    HttpOnly, SameSite=Strict cookie scoped to /api, and every response says `refreshToken: null`, so script on the
    page (an XSS bug) can never read it. The custom header is also the CSRF guard: a cross-site form can't send it,
    and the CORS allow-list stops other origins from sending it with fetch. The website and API share one origin
    (the API serves the website in production; Vite proxies /api in development).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.core.errors import Unauthorized, fail_body, ok
from app.core.validation import ValidationFailed, validate
from app.database.connection import get_db
from app.schemas.auth import (
    LOGIN_RULES,
    MFA_CODE_RULES,
    MFA_DISABLE_RULES,
    MFA_SETUP_RULES,
    MFA_VERIFY_RULES,
    OTP_REQUEST_RULES,
    OTP_VERIFY_RULES,
    PASSWORD_CHANGE_RULES,
    PASSWORD_RESET_CONFIRM_RULES,
    PASSWORD_RESET_REQUEST_RULES,
    REFRESH_RULES,
    REGISTER_RULES,
    AuthEnvelope,
    EmptyEnvelope,
    LoginEnvelope,
    LoginRequest,
    MfaCodeRequest,
    MfaDisableRequest,
    MfaSetupEnvelope,
    MfaSetupRequest,
    MfaStatusEnvelope,
    MfaVerifyRequest,
    OtpLoginRequest,
    OtpLoginVerify,
    OtpSentEnvelope,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.security.rate_limit import rate_limit
from app.services import auth_service, login_otp_service, mfa_service, password_service
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


REFRESH_COOKIE = "sr_refresh"
COOKIE_PATH = "/api"   # both /api/auth/* and /api/v1/auth/* (the browser sees the versioned path)


def _cookie_mode(request: Request) -> bool:
    return request.headers.get("x-auth-mode", "").strip().lower() == "cookie"


def _session(request: Request, response: Response, data: dict) -> dict:
    """In cookie mode, move the refresh token from the JSON body into the HttpOnly cookie."""
    if _cookie_mode(request) and data.get("refreshToken"):
        settings = request.app.state.settings
        response.set_cookie(REFRESH_COOKIE, data["refreshToken"], max_age=settings.refresh_token_expire_days * 86400,
                            path=COOKIE_PATH, httponly=True, samesite="strict",
                            secure=settings.is_production or request.url.scheme == "https")
        data = {**data, "refreshToken": None}
    return data


def _clear_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH, httponly=True, samesite="strict")


async def _refresh_token_from(request: Request) -> str:
    """The cookie in cookie mode, else the JSON body's RefreshToken (validated as before)."""
    if _cookie_mode(request):
        return request.cookies.get(REFRESH_COOKIE, "")
    return validate(await _json(request), REFRESH_RULES)["RefreshToken"]


@router.post("/register", summary="Register a Rural User account", response_model=AuthEnvelope,
             dependencies=[auth_limit], responses={k: ERRORS[k] for k in (400, 409, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": RegisterRequest.model_json_schema()}}, "required": True}})
async def register(request: Request, response: Response, db: Session = Depends(get_db)):
    body = await _json(request)
    v = validate(body, REGISTER_RULES)
    # Optional, so older clients keep working; the website requires it (DPDP: consent is recorded in the audit log).
    consent = isinstance(body, dict) and any(k.lower() == "consenttoprivacypolicy" and val is True for k, val in body.items())
    # Blocking DB work and Argon2 hashing run off the event loop.
    data = await run_in_threadpool(auth_service.register, db, request.app.state.settings, _ctx(request),
                                   v["FullName"], v["Email"], v["MobileNumber"], v["Password"], consent)
    return ok(_session(request, response, data), "Registration successful")


@router.post("/login", summary="Log in with email and password (staff with two-factor sign-in get a challenge)",
             response_model=LoginEnvelope,
             dependencies=[auth_limit], responses={k: ERRORS[k] for k in (400, 401, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": LoginRequest.model_json_schema()}}, "required": True}})
async def login(request: Request, response: Response, db: Session = Depends(get_db)):
    v = validate(await _json(request), LOGIN_RULES)
    data = await run_in_threadpool(auth_service.login, db, request.app.state.settings, _ctx(request), v["Email"], v["Password"])
    return ok(_session(request, response, data), "Login successful")


@router.post("/refresh", summary="Exchange a refresh token for new tokens (rotates it)", response_model=AuthEnvelope,
             responses={k: ERRORS[k] for k in (400, 401)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": RefreshRequest.model_json_schema()}}, "required": True}})
async def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = await _refresh_token_from(request)
    try:
        if not raw:
            raise Unauthorized(auth_service.REFRESH_INVALID)
        data = await run_in_threadpool(auth_service.refresh, db, request.app.state.settings, raw, _ctx(request))
    except Unauthorized as exc:
        if not _cookie_mode(request):
            raise
        failed = JSONResponse(status_code=401, content=fail_body(exc.message, None, exc.error_code))
        _clear_cookie(failed)   # a dead cookie is not sent again
        return failed
    return ok(_session(request, response, data), "Token refreshed")


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
async def otp_verify(request: Request, response: Response, db: Session = Depends(get_db)):
    v = validate(await _json(request), OTP_VERIFY_RULES)
    data = await run_in_threadpool(login_otp_service.verify_code, db, request.app.state.settings, _ctx(request),
                                   v["MobileNumber"], v["Otp"])
    return ok(_session(request, response, data), "Login successful")


@router.post("/logout", summary="Revoke a refresh token", response_model=EmptyEnvelope, responses={400: ERRORS[400]},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": RefreshRequest.model_json_schema()}}, "required": True}})
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = await _refresh_token_from(request)
    if raw:
        await run_in_threadpool(auth_service.logout, db, _ctx(request), raw)
    if _cookie_mode(request):
        _clear_cookie(response)
    return ok(None, "Logged out")


@router.post("/password/change", summary="Change your password (signs out every other device)", response_model=AuthEnvelope,
             dependencies=[auth_limit], responses={k: ERRORS[k] for k in (400, 401, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": PasswordChangeRequest.model_json_schema()}}, "required": True}})
async def change_password(request: Request, response: Response, user: CurrentUser = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    v = validate(await _json(request), PASSWORD_CHANGE_RULES)
    data = await run_in_threadpool(password_service.change, db, request.app.state.settings, _ctx(request), user.user_id,
                                   v["CurrentPassword"], v["NewPassword"])
    return ok(_session(request, response, data), "Password changed")


@router.post("/password/reset/request", summary="Send a password-reset code to the account's registered mobile",
             response_model=OtpSentEnvelope, dependencies=[otp_limit],
             responses={400: ERRORS[400], 429: ERRORS[429], 503: {"description": "The SMS could not be sent"}},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": PasswordResetRequest.model_json_schema()}}, "required": True}})
async def password_reset_request(request: Request, db: Session = Depends(get_db)):
    v = validate(await _json(request), PASSWORD_RESET_REQUEST_RULES)
    data = await run_in_threadpool(password_service.request_reset, db, request.app.state.settings, _ctx(request), v["MobileNumber"])
    # The same answer whether or not the number is registered (no account probing).
    return ok(data, "If this number is registered, a code has been sent.")


@router.post("/password/reset/confirm", summary="Set a new password with the code (signs out every device)",
             response_model=EmptyEnvelope, dependencies=[auth_limit, otp_limit], responses={k: ERRORS[k] for k in (400, 401, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": PasswordResetConfirm.model_json_schema()}}, "required": True}})
async def password_reset_confirm(request: Request, db: Session = Depends(get_db)):
    v = validate(await _json(request), PASSWORD_RESET_CONFIRM_RULES)
    await run_in_threadpool(password_service.confirm_reset, db, _ctx(request), v["MobileNumber"], v["Otp"], v["NewPassword"])
    return ok(None, "Password changed. Please sign in with the new password.")


# ---------------------------------------------------------------- two-factor sign-in (staff)

def _mfa_body(rules):
    async def read(request: Request) -> dict[str, str]:
        return validate(await _json(request), rules)
    return read


@router.get("/mfa/status", summary="Is two-factor sign-in on for me / available to me", response_model=MfaStatusEnvelope)
async def mfa_status(request: Request, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(await run_in_threadpool(mfa_service.status, db, request.app.state.settings, user.user_id))


@router.post("/mfa/setup", summary="Start two-factor set-up (password again): a secret for the authenticator app",
             response_model=MfaSetupEnvelope, dependencies=[auth_limit], responses={k: ERRORS[k] for k in (400, 401, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": MfaSetupRequest.model_json_schema()}}, "required": True}})
async def mfa_setup(request: Request, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    v = await _mfa_body(MFA_SETUP_RULES)(request)
    data = await run_in_threadpool(mfa_service.setup, db, request.app.state.settings, _ctx(request), user.user_id, v["Password"])
    return ok(data, "Scan the QR code with your authenticator app, then enter a code to finish.")


@router.post("/mfa/enable", summary="Finish set-up with a code: two-factor sign-in is on", response_model=MfaStatusEnvelope,
             dependencies=[auth_limit], responses={k: ERRORS[k] for k in (400, 401, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": MfaCodeRequest.model_json_schema()}}, "required": True}})
async def mfa_enable(request: Request, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    v = await _mfa_body(MFA_CODE_RULES)(request)
    data = await run_in_threadpool(mfa_service.enable, db, request.app.state.settings, _ctx(request), user.user_id, v["Code"])
    return ok(data, "Two-factor sign-in is on.")


@router.post("/mfa/disable", summary="Turn two-factor sign-in off (password and a code)", response_model=MfaStatusEnvelope,
             dependencies=[auth_limit], responses={k: ERRORS[k] for k in (400, 401, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": MfaDisableRequest.model_json_schema()}}, "required": True}})
async def mfa_disable(request: Request, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    v = await _mfa_body(MFA_DISABLE_RULES)(request)
    data = await run_in_threadpool(mfa_service.disable, db, request.app.state.settings, _ctx(request), user.user_id,
                                   v["Password"], v["Code"])
    return ok(data, "Two-factor sign-in is off.")


@router.post("/mfa/verify", summary="Second sign-in step: the code from the authenticator app", response_model=AuthEnvelope,
             dependencies=[auth_limit], responses={k: ERRORS[k] for k in (400, 401, 429)},
             openapi_extra={"requestBody": {"content": {"application/json": {"schema": MfaVerifyRequest.model_json_schema()}}, "required": True}})
async def mfa_verify(request: Request, response: Response, db: Session = Depends(get_db)):
    v = await _mfa_body(MFA_VERIFY_RULES)(request)
    data = await run_in_threadpool(mfa_service.verify, db, request.app.state.settings, _ctx(request), v["MfaToken"], v["Code"])
    return ok(_session(request, response, data), "Login successful")
