# Database Testing Completion Report — Smart Ration HSD2C

| | |
|---|---|
| Project | Smart_Ration_HSD2C_Final (Ration Mitra) |
| Location | the repository root (tests were run at `C:\Users\…\Desktop\Smart_Ration_HSD2C_Final` on 2026-09-25; the project now lives at `D:\Smart_Ration_HSD2C_Final`, where the same suites pass — 2026-09-26) |
| Branch / date | `feature/python-backend-migration` · 2026-09-25 |
| Environment | Windows 11, MySQL 8 (local, InnoDB, `utf8mb4_0900_ai_ci`), Python 3.14, .NET 8, Node/Vite 6 |
| Architecture | React/Vite frontend → Python FastAPI gateway (:8000: auth, public help, chatbot, data providers, proxy) → C# ASP.NET Core 8 business API (:5188: bookings, QR, OTP, inventory, collections) → MySQL 8; Python AI service (:8001) |
| Database | `smartration` (development; schema owned by Alembic `0001_initial`, 25 app tables + `alembic_version` + EF history) · `smartration_test` (all destructive tests) |
| Database drivers | Python: SQLAlchemy 2 + **PyMySQL**. C#: EF Core + Pomelo/**MySqlConnector** |
| MySQLi | **NOT APPLICABLE** — no PHP exists in the project, so none was installed; the equivalent tests target the real drivers above |
| Test frameworks | pytest (Python, MySQL suite, AI), xUnit (C#), Vitest + Testing Library (frontend) |

All results below are from runs on this machine on 2026-09-25. "PASS" means the tests passed under the
scenarios described; it is not a guarantee of production behaviour, which needs environment-specific validation.

## Totals

| Suite | Tests | Passed | Failed | Skipped / not run |
|---|---|---|---|---|
| Python backend (SQLite) | 201 | 201 | 0 | 144 skipped = the MySQL suite, which only runs with `TEST_DATABASE_URL` (counted on the next line) |
| MySQL suite on `smartration_test` | 146 | 146 | 0 | 0 |
| Chatbot evaluation (48 answers + 19 safety cases, en/hi/mr) | 67 | 67 | 0 | 0 |
| AI service | 46 | 46 | 0 | 0 |
| C# API | 104 | 104 | 0 | 0 |
| Frontend | 39 | 39 | 0 | 0 |
| End-to-end (Playwright, running stack) | 9 | 9 | 0 | 0 |
| **Total** | **612** | **612** | **0** | — |
| Root `tests/mysql` (24) | — | — | — | **NOT RUN** — root `.env` `DB_PASSWORD` is wrong (owner action) |
| MySQLi | — | — | — | **NOT APPLICABLE** |

Command: `.\scripts\development\run-tests.ps1 -MySql` (exit 0). Note: that full run took 89 minutes for the
MySQL suite; an immediate rerun of the same 145 tests with per-test timing took **90 s** (slowest test 13.8 s).
The cause of the slow run was not identified (no code changed between the runs); it is recorded, not explained away.

## Results by area

| Area | Result | Evidence |
|---|---|---|
| CRUD (1 / 10 / 100 / 1000 records) | PASS | `test_02` (100, via ORM and HTTP API), `test_08` (1000 citizens → 9 455 rows in 7 tables; exact counts, every value read back, 1000 updates verified, 500 + 500 deletes) ; generator tests for 1/10/100/1000/5000 |
| 1000-record test | PASS | `test_1000_synthetic_citizens_create_read_update_delete` |
| Synthetic data | PASS | central generator `app/synthetic` (deterministic by seed; reserved mobile blocks, `@example.com`, `SYN-RC-…` cards, masked Aadhaar only); 23 unit tests; CLI inserted 1000 citizens into `smartration_test` in 1.05 s, refused a rerun, refused `smartration` |
| SQL injection | PASS | 16 payloads (incl. `' OR '1'='1`, `admin'--`, `UNION SELECT`, `; DROP TABLE`) × HTTP login/register, ORM, raw driver: stored as text, no access, row counts unchanged |
| Parameterised queries | PASS | SQL text never contains values (`test_values_never_appear_in_the_sql_text`); ORM everywhere; C# EF Core |
| Unicode / Hindi / Marathi / emoji | PASS | Devanagari names round-trip at 1000 records; Marathi text appended in 1000 updates; 4-byte emoji and 150-character multibyte names (`test_07`) |
| Data integrity | PASS | no orphans after cascade deletes, UNIQUE (1062) and RESTRICT (1451) enforced at scale, timestamps set, no truncation, no duplicate codes |
| Transactions / rollback | PASS | 7-table insert is all-or-nothing; invalid batch writes nothing; deadlock victim fully rolled back (`test_05`) |
| Authentication | PASS | Argon2id, BCrypt upgrade, refresh rotation, no plaintext password in DB/API/logs (Python + C# tests) |
| Authorization (roles) | PASS | server-side role/ownership tests in both backends; chatbot personal answers only for the token's own citizen |
| QR | PASS (C#) | `QrServiceTests`, `QrScanServiceTests`: valid, tampered signature, expired, malformed, unknown token, other shop's token, cancelled booking, already collected (reuse); camera scanning NOT TESTED |
| OTP | PASS (C#) | `SyntheticOtpServiceTests`, `OtpDeliveryTests`: correct, wrong (attempts counted), too many attempts, expired, cooldown, resend invalidates the old code, SMS failure; mock SMS only. Reusing an already-verified OTP has **no dedicated test** (gap). Real SMS BLOCKED — needs a registered gateway |
| Chatbot | PASS | engine + API + UI tests, evaluation 67/67; offline/unavailable states tested |
| Concurrency (10/25/50/100) | PASS | reads, creates, lost-update check, bookings (capacity = n/2 → exactly n/2 tokens, unique numbers), stock issue (never negative) — using the C# `[ConcurrencyCheck]` pattern |
| Performance | PASS (measured) | table below; assertions are generous bounds, not benchmarks |
| Error handling | PASS | `test_06`: database down, bad credentials, timeouts, duplicates, FK violation, health without details |
| API | PASS | Python API tests; proxy parity 36/36 and auth interop 23/23 (earlier today, needs both servers) |
| Health | PASS | `/health`, `/ready`, new `/health/db` (status, latency, migrations; no connection details) — tests + live call |
| Deployment validation | PARTIAL | Docker image built and run locally (healthy, non-root, no secrets inside); compose config valid; CI runs only after the branch is pushed |

## Performance (this machine, second run)

| Operation | Total | avg / min / median / max per operation |
|---|---|---|
| Open a new MySQL connection (50×) | 1890 ms | 37.8 / 20.1 / 39.5 / 48.0 ms |
| Single trivial query (50×) | 31 ms | 0.63 / 0.42 / 0.60 / 1.02 ms |
| Insert 100 users, one transaction each | 407 ms | 200 round trips |
| Insert 100 users, one batch | 20.5 ms | 2 round trips |
| CREATE 1000 citizens (7 tables, 1 transaction, 9 455 rows) | 838 ms | — |
| READ 1000 users by primary key, one query each | 943 ms | 0.94 / 0.64 / 0.89 / 1.94 ms |
| READ 1000 users, one query | 8.4 ms | — |
| UPDATE 1000 users, one transaction each | 5103 ms | 5.10 / 4.25 / 4.96 / 34.8 ms |
| DELETE 500 citizens (cascades) | 228 ms | — |
| 100 queries, pooled vs new connection each | 77 ms vs 3959 ms | pool 52× faster |
| Concurrent reads 10 / 25 / 50 / 100 | 171 / 76 / 225 / 323 ms | — |
| Concurrent citizen creations 10 / 25 / 50 / 100 | 116 / 428 / 659 / 1155 ms | — |
| Concurrent bookings 10 / 25 / 50 / 100 (for n/2 places) | 115 / 635 / 1438 / 2648 ms | — |

Timings vary run to run and depend on the machine; they describe this run only.

## What changed in this round

- `backend/SmartRation/app/synthetic/` + `scripts/generate_test_data.py` (central, seeded generator) and `tests/integration/test_synthetic_data.py`.
- `tests/integration/mysql_suite/test_08_scale.py` (1000 records, concurrency levels), `support.stats()`.
- Demo mobiles `9876543210–12` → `9000000001 / 9000000051 / 9000000052` (both seeders, tests, dev database rows); C# `ScenarioBuilder` no longer uses random mobiles.
- `/health/db`; frontend API base falls back to localhost only in development (`/api` in production builds).
- Branding: Logo 1 (Ration Mitra emblem cropped from the supplied logo) in every header; Logo 2 (same emblem, small) in the chatbot header, avatar and launcher; favicon; HSD2C logo moved to the footer.

## Remaining risks (documented, not fixed here)

1. Root `.env` `DB_PASSWORD` is wrong → root `tests/mysql` can't run (owner action).
2. CI not executed (branch not pushed). The Docker image was built and run locally on 2026-09-25; `docker compose up` was not run.
3. Refresh token stored in `localStorage`; JWT key present in old git history (rotate before public use).
4. No end-to-end browser tests; 41 older dashboard components still English-only.
5. Real Aadhaar/ration-card/SMS integrations: BLOCKED — REQUIRES EXTERNAL INTEGRATION.
6. One unexplained 89-minute MySQL-suite run; the two later full runs took 90 s and 100 s.

## Final status

**PASS WITH MINOR ISSUES** — every automated suite passed under the defined scenarios; the items above
remain, and production readiness requires environment-specific validation.
