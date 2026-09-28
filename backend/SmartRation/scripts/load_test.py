"""HTTP load test of the RUNNING stack: N citizens using the app at the same moment.

Each virtual user signs in once (a token is minted locally, see below) and then does what a
citizen does on the dashboard, one request after another: item list with shop stock, shop list,
own bookings, own profile, search, health. All users start together, so the concurrency equals
the number of users. Requests go browser-style to the Python gateway (/api/v1), which proxies the
business routes to the C# API, which reads MySQL: the whole path is measured.

A second, small phase bursts the rate-limited public-help endpoint and checks that the limiter
answers 429 (a controlled refusal) rather than errors or timeouts.

Usage (from backend/SmartRation, with the stack running: .\\sr.ps1 run):
    .venv\\Scripts\\python scripts\\load_test.py                       # 10, 100 and 1000 users
    .venv\\Scripts\\python scripts\\load_test.py --users 10 100 --out ..\\..\\docs\\testing\\LOAD_TEST_RESULTS.md

Tokens: LOAD_TEST_TOKEN (a Bearer token for a citizen) if set; otherwise one is minted with the
local .env JWT key for the first seeded synthetic citizen. Minting is refused when ENVIRONMENT is
production. Nothing secret is printed. Read-only: no request changes data.
Exit code 0 = no failures (429s in the rate-limit phase are expected), 1 = failures.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import platform
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SCENARIO = [  # (label, path relative to the API base; {shop} = the citizen's shop)
    ("ration items + stock", "/ration/items?shopId={shop}"),
    ("shop list", "/shops"),
    ("my bookings", "/ration/bookings"),
    ("my profile", "/users/profile"),
    ("search", "/search?q=BEN"),
]
HEALTH = ("gateway liveness", "/health/live")  # root-level, unversioned; /health is a deep probe (DB + C# + AI)


@dataclass
class Result:
    label: str
    status: int  # 0 = no HTTP response (timeout / connection error)
    ms: float


@dataclass
class Run:
    users: int
    wall_s: float
    results: list[Result] = field(default_factory=list)


def citizen_token() -> tuple[str, int]:
    """(token, shop id) for the first seeded citizen, minted with the local JWT key."""
    from sqlalchemy import create_engine, text

    from app.config.settings import get_settings
    from app.security.tokens import TokenUser, create_access_token

    settings = get_settings()
    if settings.is_production:
        raise SystemExit("Refusing to mint a token with a production key; set LOAD_TEST_TOKEN instead.")
    with create_engine(settings.database_url).connect() as conn:
        row = conn.execute(text(
            "SELECT u.Id, u.Email, u.FullName, f.RationShopId FROM Users u "
            "JOIN Beneficiaries b ON b.UserId = u.Id JOIN Families f ON f.Id = b.FamilyId "
            "WHERE u.Role = 1 AND u.IsActive = 1 ORDER BY u.Id LIMIT 1")).first()
    if row is None:
        raise SystemExit("No seeded citizen found; run scripts/seed_database.py first.")
    token, _ = create_access_token(TokenUser(row.Id, row.Email, row.FullName, "RuralUser", None), settings)
    return token, row.RationShopId


class Connection:
    """One keep-alive HTTP/1.1 connection, like a browser tab. Deliberately minimal (GET only, Content-Length
    or chunked bodies): httpx's async pool slows down as it grows (about 200 req/s with 1 connection, 100 with
    100 on this machine), which would measure the load generator instead of the server."""

    def __init__(self, url: str, timeout: float) -> None:
        parts = urlsplit(url)
        self.host, self.port, self.timeout = parts.hostname or "127.0.0.1", parts.port or 80, timeout
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def get(self, url: str, headers: dict[str, str]) -> int:
        return await asyncio.wait_for(self._get(url, headers), self.timeout)

    async def _get(self, url: str, headers: dict[str, str]) -> int:
        if self.writer is None or self.writer.is_closing():
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        parts = urlsplit(url)
        target = parts.path + (f"?{parts.query}" if parts.query else "")
        head = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
        self.writer.write(f"GET {target} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\n{head}\r\n".encode())
        await self.writer.drain()
        assert self.reader is not None
        status = int((await self.reader.readline()).split()[1])
        length, chunked, close = 0, False, False
        while (line := await self.reader.readline()) not in (b"\r\n", b""):
            name, _, value = line.decode("latin-1").partition(":")
            name, value = name.strip().lower(), value.strip().lower()
            if name == "content-length":
                length = int(value)
            elif name == "transfer-encoding" and "chunked" in value:
                chunked = True
            elif name == "connection" and value == "close":
                close = True
        if chunked:
            while (size := int((await self.reader.readline()).split(b";")[0], 16)) > 0:
                await self.reader.readexactly(size + 2)
            await self.reader.readline()
        elif length:
            await self.reader.readexactly(length)
        if close:
            self.close()
        return status

    def close(self) -> None:
        if self.writer is not None:
            self.writer.close()
            self.writer = None


async def timed(conn: Connection, label: str, url: str, headers: dict[str, str]) -> Result:
    started = time.perf_counter()
    try:
        status = await conn.get(url, headers)
    except (TimeoutError, OSError, asyncio.IncompleteReadError, ValueError, IndexError):
        conn.close()
        status = 0
    return Result(label, status, (time.perf_counter() - started) * 1000)


async def virtual_user(api: str, root: str | None, token: str, shop: int, start: asyncio.Event, timeout: float) -> list[Result]:
    headers = {"Authorization": f"Bearer {token}"}
    conn = Connection(api, timeout)
    await start.wait()
    try:
        out = [await timed(conn, label, api + path.format(shop=shop), headers) for label, path in SCENARIO]
        if root is not None:
            out.append(await timed(conn, HEALTH[0], root + HEALTH[1], {}))
    finally:
        conn.close()
    return out


async def run_users(users: int, api: str, root: str | None, token: str, shop: int, timeout: float) -> Run:
    start = asyncio.Event()
    tasks = [asyncio.create_task(virtual_user(api, root, token, shop, start, timeout)) for _ in range(users)]
    await asyncio.sleep(0)  # let every user reach the start line
    began = time.perf_counter()
    start.set()
    per_user = await asyncio.gather(*tasks)
    return Run(users, time.perf_counter() - began, [r for rs in per_user for r in rs])


async def rate_limit_burst(api: str, requests: int) -> dict[int, int]:
    async def one() -> int:
        conn = Connection(api, 30)
        try:
            return (await timed(conn, "burst", f"{api}/public-help/categories?language=en", {})).status
        finally:
            conn.close()

    counts: dict[int, int] = {}
    for status in await asyncio.gather(*(one() for _ in range(requests))):
        counts[status] = counts.get(status, 0) + 1
    return counts


def pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(p / 100 * (len(ordered) - 1)))]


def summarize(run: Run) -> dict:
    ms = [r.ms for r in run.results]
    failures = [r for r in run.results if not 200 <= r.status < 300]
    return {
        "users": run.users, "requests": len(run.results), "failures": len(failures),
        "statuses": sorted({r.status for r in failures}),
        "rps": len(run.results) / run.wall_s, "wall_s": run.wall_s,
        "p50": statistics.median(ms), "p95": pct(ms, 95), "p99": pct(ms, 99), "max": max(ms),
    }


def per_endpoint(run: Run) -> list[tuple[str, float, float, int]]:
    rows = []
    for label in [s[0] for s in SCENARIO] + [HEALTH[0]]:
        ms = [r.ms for r in run.results if r.label == label]
        if not ms:
            continue
        bad = sum(1 for r in run.results if r.label == label and not 200 <= r.status < 300)
        rows.append((label, statistics.median(ms), pct(ms, 95), bad))
    return rows


def report(summaries: list[dict], runs: list[Run], burst: dict[int, int] | None, base: str) -> str:
    lines = [
        "| Users (concurrent) | Requests | Failures | Throughput (req/s) | p50 ms | p95 ms | p99 ms | max ms | Wall time |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        fail = f"{s['failures']}" + (f" (HTTP {', '.join(map(str, s['statuses']))})" if s["failures"] else "")
        lines.append(f"| {s['users']} | {s['requests']} | {fail} | {s['rps']:.0f} | {s['p50']:.0f} | {s['p95']:.0f} | "
                     f"{s['p99']:.0f} | {s['max']:.0f} | {s['wall_s']:.1f} s |")
    largest = runs[-1]
    lines += ["", f"Per endpoint at {largest.users} users (median / p95 ms, failures):", "",
              "| Endpoint | p50 ms | p95 ms | Failures |", "|---|---:|---:|---:|"]
    lines += [f"| {label} | {p50:.0f} | {p95:.0f} | {bad} |" for label, p50, p95, bad in per_endpoint(largest)]
    if burst is not None:
        lines += ["", "Rate-limit burst on `/public-help/categories` (limit 120/min per address): "
                  + ", ".join(f"HTTP {k or 'no response'} x {v}" for k, v in sorted(burst.items()))]
    lines += ["", f"Target `{base}`, {datetime.now(UTC):%Y-%m-%d %H:%M} UTC, {platform.system()} {platform.release()}, "
              f"Python {platform.python_version()}, {os.cpu_count()} logical CPUs; client and all services on the same machine."]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="http://127.0.0.1:8000/api/v1", help="API base (default: local gateway)")
    parser.add_argument("--users", type=int, nargs="+", default=[10, 100, 1000])
    parser.add_argument("--timeout", type=float, default=60.0, help="per-request timeout, seconds")
    parser.add_argument("--burst", type=int, default=200, help="requests in the rate-limit phase (0 = skip)")
    parser.add_argument("--skip-health", action="store_true", help="leave out the gateway liveness call (e.g. when --base is the C# API)")
    parser.add_argument("--out", type=Path, help="also write the results table to this Markdown file")
    args = parser.parse_args()

    api = args.base.rstrip("/")
    root = None if args.skip_health else api.rsplit("/api", 1)[0]
    token = os.environ.get("LOAD_TEST_TOKEN")
    if token:
        shop = int(os.environ.get("LOAD_TEST_SHOP_ID", "1"))
    else:
        token, shop = citizen_token()

    runs, summaries = [], []
    for users in args.users:
        run = asyncio.run(run_users(users, api, root, token, shop, args.timeout))
        summary = summarize(run)
        runs.append(run)
        summaries.append(summary)
        print(f"{users:>5} users: {summary['requests']} requests, {summary['failures']} failures, "
              f"{summary['rps']:.0f} req/s, p50 {summary['p50']:.0f} ms, p95 {summary['p95']:.0f} ms, max {summary['max']:.0f} ms")

    burst = asyncio.run(rate_limit_burst(api, args.burst)) if args.burst else None
    if burst is not None:
        print("rate-limit burst:", ", ".join(f"HTTP {k} x {v}" for k, v in sorted(burst.items())))

    table = report(summaries, runs, burst, args.base)
    print()
    print(table)
    if args.out:
        args.out.write_text(table + "\n", encoding="utf-8")
        print(f"\nWrote {args.out}")

    burst_ok = burst is None or set(burst) <= {200, 429}
    return 0 if all(s["failures"] == 0 for s in summaries) and burst_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
