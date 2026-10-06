"""Smart Ration HSD2C — Python (FastAPI) backend.

Run (from backend/SmartRation):
    .venv\\Scripts\\python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000

Migration status: routes implemented in Python are registered first; every
other /api/* request falls through to the C# API via the fallback proxy
(app/api/routes/legacy_proxy.py). See MIGRATION.md.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.ai.chatbot.knowledge_base import get_knowledge_base
from app.ai.chatbot.providers import get_provider
from app.api.routes import ai, assistant, auth, counter, government, grievances, health, legacy_proxy, people, public_help, ration
from app.api.routes.frontend import mount_frontend
from app.config.settings import Settings, get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.database.connection import configure_database, get_session_factory
from app.middleware.api_version import ApiVersionAliasMiddleware
from app.middleware.http import install_middleware
from app.security.rate_limit import FixedWindowLimiter
from app.services import slot_service
from app.services.ai_client import AiClient
from app.services.data_provider import check_data_mode

API_DESCRIPTION = """
Python backend for Smart Ration HSD2C (side-by-side migration from the C#/.NET API).

* Versioned: every route below answers under `/api/v1/...` as well as `/api/...` (same behaviour).
* Every response uses the envelope `{success, message, data, errors}`; failures add `errorCode`.
* `/api/*` routes that are not yet migrated are transparently served by the C# API
  (fallback proxy); those do not appear in this document yet.
"""


log = logging.getLogger("smartration.startup")


def _top_up_demo_slots(settings: Settings) -> None:
    """Synthetic (demo) mode: keep the next days bookable. Days that already have slots are never touched."""
    if settings.data_mode.lower() != "synthetic" or settings.upcoming_slot_days == 0:
        return
    try:
        with get_session_factory()() as db:
            added = slot_service.ensure_upcoming(db, settings.upcoming_slot_days)
        if added:
            log.info("Added %s demo time slots for the next %s days", added, settings.upcoming_slot_days)
    except Exception as exc:  # a missing table or unreachable database must not stop the API from starting
        log.warning("Could not top up demo time slots: %s", type(exc).__name__)


def create_app(settings: Settings | None = None, legacy_transport: httpx.AsyncBaseTransport | None = None,
               ai_transport: httpx.AsyncBaseTransport | None = None, ai_api_transport: httpx.BaseTransport | None = None) -> FastAPI:
    settings = settings or get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not set. See .env.example.")
    qr_problem = settings.qr_secret_problem()
    if qr_problem:  # bookings and QR verification cannot work without it; fail now, not at the first booking
        raise RuntimeError("Refusing to start: " + qr_problem)
    problems = settings.production_problems()
    if problems:  # e.g. a fixed demo OTP or a silent mock SMS provider outside development
        raise RuntimeError("Refusing to start: " + " ".join(problems))
    check_data_mode(settings.data_mode)  # real mode is BLOCKED until real integrations exist
    get_provider(settings.chatbot_provider)  # fail at startup on an unknown CHATBOT_PROVIDER
    get_knowledge_base()  # validate the Public Help content at startup, not on the first question
    configure_logging(settings.log_level)
    configure_database(settings.database_url)

    per_pool = settings.legacy_api_connections_per_pool
    legacy_clients = [
        httpx.AsyncClient(
            base_url=settings.legacy_api_url.rstrip("/"),
            timeout=settings.legacy_api_timeout_seconds,
            transport=legacy_transport,
            follow_redirects=False,
            limits=httpx.Limits(max_connections=per_pool, max_keepalive_connections=per_pool),
        )
        for _ in range(settings.legacy_api_pools if settings.legacy_api_url else 0)
    ]
    legacy_client = legacy_clients[0] if legacy_clients else None  # health checks use the first one

    ai_client = (
        httpx.AsyncClient(base_url=settings.ai_service_url.rstrip("/"), timeout=3.0, transport=ai_transport)
        if settings.ai_service_url
        else None
    )

    # Sync client for the AI analytics routes (X-Api-Key); `ai_client` above only probes /health.
    ai_api = AiClient(settings.ai_service_url, settings.ai_service_api_key, settings.ai_service_timeout_seconds, ai_api_transport)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await run_in_threadpool(_top_up_demo_slots, settings)
        yield
        for client in (*legacy_clients, ai_client):
            if client is not None:
                await client.aclose()
        ai_api.close()

    app = FastAPI(
        title="Smart Ration HSD2C API (Python)",
        version="0.1.0",
        description=API_DESCRIPTION,
        lifespan=lifespan,
        # Off outside development unless API_DOCS_ENABLED=true (no live API explorer on a public server).
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.state.legacy_client = legacy_client
    app.state.ai_client = ai_client
    app.state.ai_api = ai_api
    app.state.rate_limiter = FixedWindowLimiter()

    install_exception_handlers(app)
    install_middleware(app, settings.max_request_bytes, https_only=settings.is_production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Server-Timing"],
    )
    # Outermost: /api/v1/* is rewritten to /api/* before anything else sees the request.
    app.add_middleware(ApiVersionAliasMiddleware)

    # ---- Python-native routes (grow with each migration phase) ----
    app.include_router(health.router)
    app.include_router(auth.router)  # Step 2: /api/auth/{register,login,refresh,logout}
    app.include_router(public_help.router)  # new: /api/public-help/*, /api/chatbot/* (no login)
    app.include_router(ration.router)  # items, shops, slots, bookings/tokens, token QR
    app.include_router(counter.router)  # scanner, shop, verification/OTP, collection, inventory, notifications
    app.include_router(people.router)  # own profile, beneficiaries, families, search, public badge
    app.include_router(ai.router)  # AI analytics / alerts / OCR (optional AI service, rule-based fallback)
    app.include_router(government.router)  # admin dashboard, statistics, reports, users, map, database viewer
    app.include_router(grievances.router)  # citizens' complaints with reference numbers; officials' review
    app.include_router(assistant.router)  # the app's AI button: understand -> one checked action

    # ---- Fallback proxy: MUST stay last ----
    if legacy_client is not None:
        app.include_router(legacy_proxy.build_router(legacy_clients))

    # ---- The built website (optional): registered after every API route ----
    if settings.frontend_dist_dir:
        mount_frontend(app, settings.frontend_dist_dir)

    return app
