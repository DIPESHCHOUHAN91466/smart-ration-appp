"""Health endpoints for the Python backend itself.

GET /health        -> liveness + database + legacy C# API reachability.
GET /health/live   -> process is up (no dependencies checked).

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

from app.db.database import database_is_reachable

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = Field(description="healthy | degraded | unhealthy")
    database: str = Field(description="healthy | unhealthy")
    legacyApi: str = Field(description="healthy | unhealthy | disabled — the C# API behind the fallback proxy")


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

    client: httpx.AsyncClient | None = request.app.state.legacy_client
    if client is None:
        legacy = "disabled"
    else:
        try:
            reply = await client.get("/health", timeout=3.0)
            legacy = "healthy" if reply.status_code == 200 else "unhealthy"
        except httpx.HTTPError:
            legacy = "unhealthy"

    status = "unhealthy" if not database else "healthy" if legacy in ("healthy", "disabled") else "degraded"
    body = HealthResponse(status=status, database="healthy" if database else "unhealthy", legacyApi=legacy)
    return JSONResponse(status_code=200 if database else 503, content=body.model_dump())
