"""Health endpoints for the Python backend itself.

GET /health        -> overall status: database, legacy C# API, AI service, chatbot, data mode.
GET /health/db     -> database only: reachable, query latency, migrations at head.
GET /health/live   -> process is up (no dependencies checked).
GET /ready         -> 200 only when the app can serve traffic: database reachable,
                      schema at the Alembic head this code expects, and (while
                      routes are still proxied) the legacy C# API reachable.

`/api/health` is NOT defined here yet: until the health area is migrated it
is served by the C# API through the fallback proxy, so the frontend's
existing health check keeps its current response shape.
"""

from __future__ import annotations

import asyncio
import time

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.chatbot.knowledge_base import get_knowledge_base
from app.chatbot.providers import get_provider
from app.db.database import alembic_head, current_revision, database_is_reachable

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = Field(description="healthy | degraded | unhealthy")
    database: str = Field(description="healthy | unhealthy")
    legacyApi: str = Field(description="healthy | unhealthy | disabled — the C# API behind the fallback proxy")
    aiService: str = Field(description="healthy | unhealthy | disabled — the Python AI/analytics service")
    chatbot: str = Field(description="healthy | unhealthy — knowledge base loaded and provider available")
    dataMode: str = Field(description="synthetic | real")


class ReadyResponse(BaseModel):
    ready: bool
    checks: dict[str, str] = Field(description="database, migrations, legacyApi: ok | failing | disabled (+ detail)")


async def _probe(client: httpx.AsyncClient | None, path: str = "/health") -> str:
    if client is None:
        return "disabled"
    try:
        reply = await client.get(path, timeout=3.0)
        return "healthy" if reply.status_code == 200 else "unhealthy"
    except httpx.HTTPError:
        return "unhealthy"


def _chatbot_status(settings) -> str:
    try:
        get_knowledge_base()
        get_provider(settings.chatbot_provider)
        return "healthy"
    except Exception:
        return "unhealthy"


async def _legacy_status(request: Request) -> str:
    client: httpx.AsyncClient | None = request.app.state.legacy_client
    if client is None:
        return "disabled"
    try:
        reply = await client.get("/health", timeout=3.0)
        return "healthy" if reply.status_code == 200 else "unhealthy"
    except httpx.HTTPError:
        return "unhealthy"


@router.get(
    "/ready",
    summary="Readiness probe (database, migration version, legacy API)",
    response_model=ReadyResponse,
    responses={503: {"model": ReadyResponse, "description": "Not ready"}},
)
async def ready(request: Request):
    database = await asyncio.to_thread(database_is_reachable)
    current = await asyncio.to_thread(current_revision) if database else None
    head = alembic_head()
    legacy = await _legacy_status(request)
    checks = {
        "database": "ok" if database else "failing",
        "migrations": "ok" if database and current == head else f"failing (database at {current}, code expects {head})",
        "legacyApi": {"healthy": "ok", "disabled": "disabled"}.get(legacy, "failing"),
    }
    is_ready = all(v in ("ok", "disabled") for v in checks.values())
    return JSONResponse(status_code=200 if is_ready else 503, content=ReadyResponse(ready=is_ready, checks=checks).model_dump())


class DatabaseHealthResponse(BaseModel):
    status: str = Field(description="healthy | unhealthy")
    latencyMs: float | None = Field(description="round trip of a trivial query; null when unreachable")
    migrations: str = Field(description="ok | behind | unknown — schema at the Alembic head this code expects")


@router.get(
    "/health/db",
    summary="Database health (no connection details are returned)",
    response_model=DatabaseHealthResponse,
    responses={503: {"model": DatabaseHealthResponse, "description": "Database unreachable"}},
)
async def database_health():
    started = time.perf_counter()
    reachable = await asyncio.to_thread(database_is_reachable)
    latency = round((time.perf_counter() - started) * 1000, 1) if reachable else None
    current = await asyncio.to_thread(current_revision) if reachable else None
    migrations = "unknown" if not reachable else "ok" if current == alembic_head() else "behind"
    body = DatabaseHealthResponse(status="healthy" if reachable else "unhealthy", latencyMs=latency, migrations=migrations)
    return JSONResponse(status_code=200 if reachable else 503, content=body.model_dump())


@router.get("/health/live", summary="Liveness probe", response_model=dict)
async def live() -> dict:
    return {"status": "healthy"}


@router.get(
    "/health",
    summary="Readiness: database and legacy API",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "Database unreachable"}},
)
async def health(request: Request):
    database = await asyncio.to_thread(database_is_reachable)

    legacy = await _legacy_status(request)
    ai = await _probe(request.app.state.ai_client)
    settings = request.app.state.settings
    chatbot = _chatbot_status(settings)
    dependencies_ok = legacy in ("healthy", "disabled") and ai in ("healthy", "disabled") and chatbot == "healthy"
    status = "unhealthy" if not database else "healthy" if dependencies_ok else "degraded"
    body = HealthResponse(status=status, database="healthy" if database else "unhealthy", legacyApi=legacy,
                          aiService=ai, chatbot=chatbot, dataMode=settings.data_mode)
    return JSONResponse(status_code=200 if database else 503, content=body.model_dump())
