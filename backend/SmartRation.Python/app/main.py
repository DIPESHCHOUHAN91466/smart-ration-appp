"""Smart Ration HSD2C — Python (FastAPI) backend.

Run (from backend/SmartRation.Python):
    .venv\\Scripts\\python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000

Migration status: routes implemented in Python are registered first; every
other /api/* request falls through to the C# API via the fallback proxy
(app/api/legacy_proxy.py). See MIGRATION.md.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, legacy_proxy, public_help
from app.chatbot.knowledge_base import get_knowledge_base
from app.chatbot.providers import get_provider
from app.core.api_version import ApiVersionAliasMiddleware
from app.core.config import Settings, get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import install_middleware
from app.core.rate_limit import FixedWindowLimiter
from app.data_providers import check_data_mode
from app.db.database import configure_database
from app.web import mount_frontend

API_DESCRIPTION = """
Python backend for Smart Ration HSD2C (side-by-side migration from the C#/.NET API).

* Versioned: every route below answers under `/api/v1/...` as well as `/api/...` (same behaviour).
* Every response uses the envelope `{success, message, data, errors}`; failures add `errorCode`.
* `/api/*` routes that are not yet migrated are transparently served by the C# API
  (fallback proxy); those do not appear in this document yet.
"""


def create_app(settings: Settings | None = None, legacy_transport: httpx.AsyncBaseTransport | None = None,
               ai_transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    settings = settings or get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not set (it must equal the C# API's user-secret Jwt:Key). See .env.example.")
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

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        for client in (*legacy_clients, ai_client):
            if client is not None:
                await client.aclose()

    app = FastAPI(
        title="Smart Ration HSD2C API (Python)",
        version="0.1.0",
        description=API_DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.settings = settings
    app.state.legacy_client = legacy_client
    app.state.ai_client = ai_client
    app.state.rate_limiter = FixedWindowLimiter()

    install_exception_handlers(app)
    install_middleware(app, settings.max_request_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    # Outermost: /api/v1/* is rewritten to /api/* before anything else sees the request.
    app.add_middleware(ApiVersionAliasMiddleware)

    # ---- Python-native routes (grow with each migration phase) ----
    app.include_router(health.router)
    app.include_router(auth.router)  # Step 2: /api/auth/{register,login,refresh,logout}
    app.include_router(public_help.router)  # new: /api/public-help/*, /api/chatbot/* (no login)

    # ---- Fallback proxy: MUST stay last ----
    if legacy_client is not None:
        app.include_router(legacy_proxy.build_router(legacy_clients))

    # ---- The built website (optional): registered after every API route ----
    if settings.frontend_dist_dir:
        mount_frontend(app, settings.frontend_dist_dir)

    return app
