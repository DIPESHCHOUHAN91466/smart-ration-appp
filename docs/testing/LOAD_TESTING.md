# Load testing (HTTP)

Measured 2026-09-26 on the development laptop: Windows 11, 12 logical CPUs, Python 3.14.7, local MySQL 8,
C# API as `dotnet run` (Debug, Development). **The load generator and all four services share one machine**,
so absolute numbers are a floor, not a production forecast. What they show reliably: where the bottleneck
is, and whether anything fails under load.

## How to run

```powershell
.\sr.ps1 run                      # start the stack (or the four services any other way)
.\sr.ps1 load                     # 10, 100 and 1000 concurrent users + a rate-limit burst
.\sr.ps1 load --users 50 --burst 0 --out ..\..\docs\testing\my-run.md
.\sr.ps1 load --users 100 --skip-health --base http://127.0.0.1:5188/api   # the C# API alone, for comparison
```

`backend/SmartRation/scripts/load_test.py`. Each virtual user is a signed-in citizen with its own
keep-alive connection (like a browser tab) who, one request after another, loads the item list with shop
stock, the shop list, their bookings, their profile, a search, and the gateway's liveness check. All users
start at the same instant, so concurrency = users. Requests go to the Python gateway at `/api/v1`, which
proxies to C#, which reads MySQL: the whole path is measured. **Read-only**: nothing is booked or changed.

The token is minted with the local `.env` JWT key for the first seeded synthetic citizen (refused when
`ENVIRONMENT=production`; set `LOAD_TEST_TOKEN` to test another deployment). Nothing secret is printed.
Exit code 1 if any request fails (429s in the rate-limit burst are expected, not failures).

## Results (after the fixes below)

| Users (concurrent) | Requests | Failures | Throughput (req/s) | p50 ms | p95 ms | p99 ms | max ms | Wall time |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 60 | 0 | 364 | 22 | 53 | 54 | 54 | 0.2 s |
| 100 | 600 | 0 | 371 | 256 | 463 | 518 | 778 | 1.6 s |
| 1000 | 6000 | 0 | 270 | 2192 | 8734 | 12826 | 20056 | 22.3 s |

Per endpoint at 1000 users: item list with stock p50 4.2 s (the heaviest: items + stock + the citizen's
entitlement), shop list 2.9 s, bookings 2.8 s, profile 2.5 s, search 1.8 s, gateway liveness 0.19 s.

**Rate limiting under a burst** (200 simultaneous `GET /api/v1/public-help/categories`, limit 120/min per
address): exactly 120 × 200 and 80 × 429. The limiter refuses cleanly: no errors, no timeouts.

**The C# API alone** (same scenario, called directly): 1000 users → 1231 req/s, p50 590 ms, p95 1.7 s,
0 failures. So at 1000 users the remaining limit is the single Python gateway process, not C# or MySQL.

Summary: **no request failed at 10, 100 or 1000 concurrent users.** At 10 and 100 users responses are fast
(p95 under 0.5 s). At 1000 users every request still succeeds, but slowly (p95 8.7 s): that is the point to
scale out (below).

## Found and fixed while testing

| # | Finding | Effect | Fix |
|---|---|---|---|
| 1 | `anyio` 4.15 no longer installs `sniffio`, but `httpcore` 1.0.9 imports it inside a function on every connection-pool lock. A failed import is not cached, so **every proxied request searched the whole Python path on disk** (~25 filesystem lookups) | ~5 ms of wasted CPU per request to C#; 10 users: p50 74 ms | `sniffio==1.3.1` pinned in `requirements.txt` → p50 43 ms |
| 2 | `httpcore`'s pool matches every waiting request against every connection, so its cost grows with the square of concurrency: one pool with 100 connections served ~90 req/s, one with 10 served ~440 | the gateway, not C#, capped the system at ~130 req/s | the proxy now uses **8 small pools × 8 connections, in turn** (`LEGACY_API_POOLS`, `LEGACY_API_CONNECTIONS_PER_POOL`); 100 users: 133 → 371 req/s, p95 1.97 s → 0.46 s |
| 3 | `/health` is a deep check (database + C# + AI) | a poor per-user call; fine for monitors | the test uses `/health/live`; nothing to change in the product |
| 4 | the load generator itself (httpx async) was slower than the server | would have measured the tool | the tool uses a minimal keep-alive HTTP/1.1 client instead |

## What to do before real traffic (NOT DONE — recommendations)

1. **More gateway processes.** Run uvicorn with several workers (or several instances behind the load
   balancer). NOT VERIFIED here. Caveat: the rate limiter keeps its counters in memory per process, so with
   N processes each address effectively gets N× the limit. For several processes, move the counters to a
   shared store (for example Redis) first.
2. **Measure on production-like hardware**, with the C# API as the Release Docker image, and the load
   generator on another machine. Render's free plan (0.1 CPU) will be far slower than this laptop.
3. The item list with stock is the heaviest call (several queries per request); a short cache of the
   catalog and stock per shop is the first optimisation if it becomes the limit.

## Not covered

Write paths under load (bookings, collections) are covered at the database level instead: the MySQL
suite runs 10/25/50/100 concurrent bookings and stock issues and checks that capacity and stock are never
exceeded (see [TESTING.md](TESTING.md)). Sign-in is rate-limited to 10/min per address by design, so it is
not load-tested from one machine.
