"""API versioning: /api/v1/* is the versioned name for /api/*.

Rewrites the path before routing, so every route (the Python ones and those the proxy forwards to
the C# API) answers under both prefixes with identical behaviour: same auth, rate limits, errors
and logs. /api/* stays as it is, so existing clients keep working. A future breaking change would
get /api/v2 with its own routes; v1 then keeps meaning today's contract.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send

VERSIONED_PREFIX = "/api/v1"
UNVERSIONED_PREFIX = "/api"


def strip_version(path: str) -> str | None:
    """'/api/v1/x' -> '/api/x', '/api/v1' -> '/api'; anything else (including '/api/v10') -> None."""
    if path == VERSIONED_PREFIX or path.startswith(VERSIONED_PREFIX + "/"):
        return UNVERSIONED_PREFIX + path[len(VERSIONED_PREFIX):]
    return None


class ApiVersionAliasMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            path = strip_version(scope["path"])
            if path is not None:
                scope = dict(scope)
                scope["path"] = path
                raw = scope.get("raw_path")
                if raw is not None:
                    scope["raw_path"] = raw.replace(VERSIONED_PREFIX.encode(), UNVERSIONED_PREFIX.encode(), 1)
        await self.app(scope, receive, send)
