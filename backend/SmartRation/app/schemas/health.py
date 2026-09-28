"""Response models of the health endpoints (/health, /ready, /health/db) for OpenAPI.

They carry states only (healthy / unhealthy / disabled, ok / failing), never hosts, URLs or credentials.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


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


class DatabaseHealthResponse(BaseModel):
    status: str = Field(description="healthy | unhealthy")
    latencyMs: float | None = Field(description="round trip of a trivial query; null when unreachable")
    migrations: str = Field(description="ok | behind | unknown — schema at the Alembic head this code expects")
