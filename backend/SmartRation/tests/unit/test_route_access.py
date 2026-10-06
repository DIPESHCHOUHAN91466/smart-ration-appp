"""Deny by default: every API route needs a signed-in user unless it is on this reviewed public list. A new route
that forgets `Depends(get_current_user)` (directly or through actor()/require_roles()) fails here."""

from __future__ import annotations

from fastapi.routing import APIRoute
from py_testkit import make_settings

from app.main import create_app

PUBLIC = {
    # health and readiness probes (no personal data; tests/api/test_health_and_errors.py)
    ("GET", "/ready"), ("GET", "/health"), ("GET", "/health/db"), ("GET", "/health/live"), ("GET", "/api/health"),
    # signing in, and the steps before a session exists
    ("POST", "/api/auth/register"), ("POST", "/api/auth/login"), ("POST", "/api/auth/refresh"), ("POST", "/api/auth/logout"),
    ("POST", "/api/auth/otp/request"), ("POST", "/api/auth/otp/verify"),
    ("POST", "/api/auth/password/reset/request"), ("POST", "/api/auth/password/reset/confirm"), ("POST", "/api/auth/mfa/verify"),
    # public help and chatbot (reviewed knowledge base; rate limited)
    ("GET", "/api/public-help/categories"), ("GET", "/api/public-help/articles/{article_id}"), ("GET", "/api/public-help/search"),
    ("GET", "/api/chatbot/welcome"), ("POST", "/api/chatbot/message"),
    # verification badge: non-sensitive fields only (profile_service.public_badge)
    ("GET", "/api/public/beneficiaries/{reference}"),
}


def _routes(routes, prefix=""):
    for route in routes:
        if isinstance(route, APIRoute):
            yield prefix, route
        elif hasattr(route, "original_router"):        # FastAPI's included-router wrapper
            context = getattr(route, "include_context", None)
            yield from _routes(route.original_router.routes, prefix + (getattr(context, "prefix", "") or ""))


def _dependencies(dependant, found):
    for sub in dependant.dependencies:
        found.add(getattr(sub.call, "__qualname__", repr(sub.call)))
        _dependencies(sub, found)
    return found


def test_only_reviewed_routes_are_public(tmp_path):
    app = create_app(make_settings(tmp_path, legacy_api_url=""))
    public, total = set(), 0
    for prefix, route in _routes(app.routes):
        total += 1
        if not any(name.startswith("get_current_user") for name in _dependencies(route.dependant, set())):
            public |= {(method, prefix + route.path) for method in route.methods}
    assert total > 80                                     # the walk really saw the API
    assert public - PUBLIC == set(), "new public routes: sign-in required by default; review and list them here"
    assert PUBLIC - public == set(), "listed as public but now protected (or removed): update the list"
