"""Live contract check: every call made DIRECTLY to the C# API and THROUGH the
Python fallback proxy must return the same status code and the same JSON.

Not part of the unit test run (needs both servers). Usage:
    .venv\\Scripts\\python tests\\contract\\compare_proxy.py
Env: LEGACY_URL (default http://localhost:5188), PYTHON_URL (default http://127.0.0.1:8000).
Demo accounts only (password demo123). Read-only calls, except login.
"""

from __future__ import annotations

import os
import sys

import httpx

LEGACY = os.getenv("LEGACY_URL", "http://localhost:5188")
PYTHON = os.getenv("PYTHON_URL", "http://127.0.0.1:8000")

# Values that legitimately differ between two calls made a moment apart.
VOLATILE_KEYS = {"generated_at", "local_time", "generatedAt", "lastAnalysisAt", "lastSeenAt"}


def login(email: str) -> str:
    r = httpx.post(f"{LEGACY}/api/auth/login", json={"email": email, "password": "demo123"}, timeout=30)
    r.raise_for_status()
    return r.json()["data"]["accessToken"]


def normalize(value):
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items() if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def compare(method: str, path: str, token: str | None = None, **kwargs) -> tuple[bool, str]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    a = httpx.request(method, f"{LEGACY}{path}", headers=headers, timeout=60, **kwargs)
    b = httpx.request(method, f"{PYTHON}{path}", headers=headers, timeout=60, **kwargs)
    try:
        ja, jb = normalize(a.json()), normalize(b.json())
    except ValueError:
        ja, jb = a.text, b.text
    # Migrated routes are answered by Python itself; everything else must be proxied.
    served = b.headers.get("X-Served-By", "python")
    if isinstance(ja, dict) and isinstance(jb, dict) and ja.get("errors") and jb.get("errors"):
        ja["errors"], jb["errors"] = sorted(ja["errors"]), sorted(jb["errors"])
    same = a.status_code == b.status_code and ja == jb
    detail = f"{a.status_code}/{b.status_code} via {served}"
    if not same and a.status_code == b.status_code:
        detail += " BODY DIFFERS"
    return same, detail


def main() -> int:
    rural, shop, gov = login("rural@example.com"), login("shop@example.com"), login("officer@example.com")
    cases = [
        # anonymous / auth failures
        ("GET", "/api/ration/items", None),
        ("GET", "/api/tokens/today", None),                      # 401
        ("POST", "/api/auth/login", None, {"json": {"email": "nobody@example.com", "password": "wrong"}}),  # 401
        ("POST", "/api/auth/login", None, {"json": {}}),          # 400 validation
        ("GET", "/api/public/beneficiaries/NOPE", None),
        # rural user
        ("GET", "/api/users/profile", rural),
        ("GET", "/api/beneficiaries/me", rural),
        ("GET", "/api/ration/bookings", rural),
        ("GET", "/api/ration/bookings/126", rural),
        ("GET", "/api/tokens/126", rural),
        ("GET", "/api/qr/payload/126", rural),
        ("GET", "/api/notifications", rural),
        ("GET", "/api/shops", rural),
        ("GET", "/api/slots?shopId=1&date=2026-09-24", rural),
        ("GET", "/api/tokens/today", rural),                      # 403 (shop only)
        ("GET", "/api/ai/analytics/risk", rural),                 # 403
        # shop owner
        ("GET", "/api/shop/dashboard", shop),
        ("GET", "/api/shop/queue", shop),
        ("GET", "/api/tokens/today", shop),
        ("GET", "/api/inventory", shop),
        ("GET", "/api/verification/qr/SRQR-51-D4E53735162078E9", shop),
        ("GET", "/api/beneficiaries/1/full-profile", shop),
        ("GET", "/api/ai/alerts/list?status=all", shop),
        ("GET", "/api/ration/bookings/999999", rural),            # 404
        # government
        ("GET", "/api/admin/dashboard", gov),
        ("GET", "/api/admin/statistics", gov),
        ("GET", "/api/admin/users", gov),
        ("GET", "/api/admin/database/tables", gov),
        ("GET", "/api/shops/map", gov),
        ("GET", "/api/government/map/analytics", gov),
        ("GET", "/api/audit/verification", gov),
        ("GET", "/api/search?q=Rahul", gov),
        ("GET", "/api/ai/intelligence-center", gov),
        ("GET", "/api/ai/analytics/forecast?horizonDays=30", gov),
        ("GET", "/api/ai/alerts/list?status=active", gov),
        ("GET", "/api/health", None),
    ]
    failures = 0
    for case in cases:
        method, path, token = case[:3]
        kwargs = case[3] if len(case) > 3 else {}
        same, detail = compare(method, path, token, **kwargs)
        failures += not same
        print(f"{'OK  ' if same else 'FAIL'} {method:4} {path:55} {detail}")
    print(f"\n{len(cases) - failures}/{len(cases)} identical")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
