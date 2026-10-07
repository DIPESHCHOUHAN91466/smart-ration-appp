# Load test

`load_test.py` simulates N users at once, each repeating a citizen's dashboard reads (notifications, bookings,
ration-card profile) with **no pause between requests**. Read-only; it signs in once and reuses the token.
Never run it against production.

```powershell
backend\SmartRation\.venv\Scripts\python tests\load\load_test.py --base-url http://127.0.0.1:8000 --users 10 50 100 250 500
```

## Results: 2026-10-07, local

One API process (as in the Docker image), local MySQL, Windows laptop (7.4 GB RAM, an Android emulator also
running), 20 s per step:

| Simulated users | Requests | Requests/s | Median | 95th % | 99th % | Errors |
|---|---|---|---|---|---|---|
| 10 | 1,631 | 82 | 127 ms | 197 ms | 232 ms | 0 |
| 50 | 1,666 | 83 | 605 ms | 853 ms | 952 ms | 0 |
| 100 | 1,763 | 88 | 1.2 s | 1.7 s | 1.9 s | 0 |
| 250 | 1,892 | 95 | 2.7 s | 4.4 s | 4.7 s | 0 |
| 500 | 1,601 | 80 | 7.2 s | 16 s | 21 s | 10 (connection reset) |

1,000 was not run: at 500 the server is saturated and starts dropping connections; the API was healthy again
right after.

## What it means

- **Capacity: about 90 requests per second** for one API process here. Above ~50 back-to-back users, more load
  only adds waiting time. A real citizen makes a request every few seconds, not continuously, so this is roughly
  several hundred people actively using the site at the same moment.
- The cloud demo will be **much slower**: Render's free plan gives a fraction of one CPU and sleeps when idle. Run
  this against the staging URL before sizing production (`--base-url https://<staging>`).
- To scale: a paid instance with 2+ CPUs and `--workers` matching them (each worker needs its own memory and
  database connections), then more instances behind Render's load balancer. Rate limits are per process today;
  with several instances they need a shared store (e.g. Redis) to stay exact.
- Per-address rate limits (e.g. public help 120/min) answer 429 to this test because all simulated users share one
  address. Real users don't; public pages are therefore left out of the mix.
