"""Load test: N simulated users at once, each repeating a citizen's typical reads for a fixed time.

    backend/SmartRation/.venv/Scripts/python tests/load/load_test.py --base-url http://127.0.0.1:8000 --users 10 50 100

Signs in once as the demo citizen (password from E2E_DEMO_PASSWORD, or the README row when run locally) and reuses
that access token, so the sign-in rate limit is not what gets measured. Read-only: it creates no data.
Only for local or staging servers; never point it at production.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import statistics
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
CITIZEN = "rural@example.com"
# What a citizen's dashboard loads. (Public pages are left out: their per-address rate limits would answer 429,
# since every simulated user here shares one address, unlike real citizens.)
PATHS = ["/api/notifications", "/api/ration/bookings", "/api/beneficiaries/me"]


def demo_password() -> str:
    if os.environ.get("E2E_DEMO_PASSWORD"):
        return os.environ["E2E_DEMO_PASSWORD"]
    row = next(line for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines() if f"`{CITIZEN}`" in line)
    return re.findall(r"`([^`]+)`", row)[1]


async def user(client: httpx.AsyncClient, token: str, until: float, times: list[float], errors: list[str]) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    i = 0
    while time.perf_counter() < until:
        path = PATHS[i % len(PATHS)]
        i += 1
        start = time.perf_counter()
        try:
            r = await client.get(path, headers=headers)
            if r.status_code >= 400:
                errors.append(str(r.status_code))
        except httpx.HTTPError as e:
            errors.append(type(e).__name__)
        times.append(time.perf_counter() - start)


async def run(base_url: str, users: int, seconds: float, token: str) -> dict:
    times: list[float] = []
    errors: list[str] = []
    limits = httpx.Limits(max_connections=users, max_keepalive_connections=users)
    async with httpx.AsyncClient(base_url=base_url, timeout=30, limits=limits) as client:
        until = time.perf_counter() + seconds
        await asyncio.gather(*(user(client, token, until, times, errors) for _ in range(users)))
    ordered = sorted(times)
    pick = lambda q: ordered[min(len(ordered) - 1, int(q * len(ordered)))] * 1000
    return {
        "users": users, "requests": len(times), "per_second": len(times) / seconds,
        "p50_ms": statistics.median(ordered) * 1000, "p95_ms": pick(0.95), "p99_ms": pick(0.99),
        "errors": len(errors), "error_kinds": sorted(set(errors)),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--users", type=int, nargs="+", default=[10, 50, 100])
    parser.add_argument("--seconds", type=float, default=20)
    args = parser.parse_args()
    async with httpx.AsyncClient(base_url=args.base_url, timeout=30) as client:
        r = await client.post("/api/auth/login", json={"email": CITIZEN, "password": demo_password()})
        r.raise_for_status()
        token = r.json()["data"]["accessToken"]
    print(f"{'users':>6} {'requests':>9} {'req/s':>7} {'p50 ms':>7} {'p95 ms':>7} {'p99 ms':>7} {'errors':>7}")
    for n in args.users:
        s = await run(args.base_url, n, args.seconds, token)
        print(f"{s['users']:>6} {s['requests']:>9} {s['per_second']:>7.1f} {s['p50_ms']:>7.0f} {s['p95_ms']:>7.0f} "
              f"{s['p99_ms']:>7.0f} {s['errors']:>7} {' '.join(s['error_kinds'])}")


if __name__ == "__main__":
    asyncio.run(main())
