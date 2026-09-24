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

from app.api import health, legacy_proxy
from app.core.config import Settings, get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import install_middleware
from app.db.database import configure_database

API_DESCRIPTION = """
Python backend for Smart Ration HSD2C (side-by-side migration from the C#/.NET API).

* Every response uses the envelope `{success, message, data, errors}`; failures add `errorCode`.
* `/api/*` routes that are not yet migrated are transparently served by the C# API
  (fallback proxy); those do not appear in this document yet.
"""


def create_app(settings: Settings | None = None, legacy_transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    configure_database(settings.database_url)

    legacy_client = (
        httpx.AsyncClient(
            base_url=settings.legacy_api_url.rstrip("/"),
            timeout=settings.legacy_api_timeout_seconds,
            transport=legacy_transport,
            follow_redirects=False,
        )
        if settings.legacy_api_url
        else None
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if legacy_client is not None:
            await legacy_client.aclose()

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

    install_exception_handlers(app)
    install_middleware(app, settings.max_request_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    # ---- Python-native routes (grow with each migration phase) ----
    app.include_router(health.router)

    # ---- Fallback proxy: MUST stay last ----
    if legacy_client is not None:
        app.include_router(legacy_proxy.build_router(legacy_client))

    return app
