"""Health endpoints for the Python backend itself.

GET /health        -> liveness + database + legacy C# API reachability.
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

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.db.database import alembic_head, current_revision, database_is_reachable

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = Field(description="healthy | degraded | unhealthy")
    database: str = Field(description="healthy | unhealthy")
    legacyApi: str = Field(description="healthy | unhealthy | disabled — the C# API behind the fallback proxy")


class ReadyResponse(BaseModel):
    ready: bool
    checks: dict[str, str] = Field(description="database, migrations, legacyApi: ok | failing | disabled (+ detail)")


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
    status = "unhealthy" if not database else "healthy" if legacy in ("healthy", "disabled") else "degraded"
    body = HealthResponse(status=status, database="healthy" if database else "unhealthy", legacyApi=legacy)
    return JSONResponse(status_code=200 if database else 503, content=body.model_dump())
