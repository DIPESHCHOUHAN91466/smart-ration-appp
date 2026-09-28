# Smart Ration HSD2C — Project Status

Date: 2026-09-25 · Branch `feature/python-backend-migration` (not pushed) · Audit: [PROJECT_AUDIT.md](PROJECT_AUDIT.md)

**PASS** = verified by automated tests and/or in the browser during this work · **PARTIAL** = works but
incomplete or only partly verified · **FAIL** = broken · **NOT TESTED** = not verified ·
**BLOCKED** = requires an external integration that doesn't exist.

## Frontend

| Item | Status | Evidence |
|---|---|---|
| Production build | PASS | `npm run build` (main bundle ≈ 520 KB, above Vite's 500 KB advisory) |
| Component tests | PASS | Vitest 39/39 |
| Logo 1 (Ration Mitra emblem, cropped from the supplied logo) in every header; HSD2C in the footer | PASS | browser: landing (desktop + 375 px), login; dashboard sidebar by code only (no sign-in performed) |
| Logo 2 (same emblem, small) in chatbot header/avatar/launcher; favicon | PASS | browser + chatbot tests |
| Production API base never falls back to localhost | PASS | `apiBase.test.js` |
| Landing page, Public Help, status page | PASS | browser (desktop + 375 px; en/hi/mr); tests |
| Citizen dashboard via the Python API | PASS | browser: login → dashboard, all calls 200, no console errors |
| Shop and government screens | PARTIAL | APIs 200 through the proxy (parity 36/36); screens not re-checked visually this round |
| Layout kept, every folder documented | PASS | READMEs in `frontend/`, `src/*`, `tests/` |
| TypeScript | NOT TESTED | not used (JavaScript app) |
| End-to-end browser automation | PASS | Playwright, 9 tests (desktop + phone) against the running stack, installed Edge |

## Backend (C# business API)

| Item | Status | Evidence |
|---|---|---|
| Build + tests | PASS | xUnit 94/94 (8 new data-mode tests) |
| Business logic owner (frozen hybrid) | PASS | decision recorded; proxy parity 36/36 |
| Controllers thin, services + interfaces; no repository layer (by design) | PASS | last two fat controllers moved into services (+10 tests); documented in BACKEND_ARCHITECTURE.md |
| Data-mode guard | PASS | real mode refused at startup (verified by running the API with `DATA_MODE=real`) |

## Python

| Item | Status | Evidence |
|---|---|---|
| Python API (gateway, auth, chatbot, data providers, migrations) | PASS | pytest 195/195; ruff + mypy clean |
| AI service | PASS | pytest 46/46; `/health` 200 |
| Package structure, type hints, config via environment | PASS | see PYTHON_ARCHITECTURE.md |

## MySQL

| Item | Status | Evidence |
|---|---|---|
| `smartration`: 25 tables, Alembic `0001_initial`, 0 drift | PASS | `verify_database.py` |
| MySQL suite on `smartration_test` (CRUD, injection, performance, concurrency, errors, integrity, 1000 records, concurrency 10/25/50/100) | PASS | 145/145 via `run-tests.ps1 -MySql`; see [docs/testing/DATABASE_TESTING_COMPLETION_REPORT.md](../docs/testing/DATABASE_TESTING_COMPLETION_REPORT.md) |
| Root `tests/mysql` | PARTIAL | 24/24 with the correct password; your root `.env` `DB_PASSWORD` is still wrong |
| Backup | PASS (2026-09-24) · Restore | NOT TESTED |

## Authentication

| Item | Status | Evidence |
|---|---|---|
| Register, login, refresh, logout; Argon2id; BCrypt upgrade | PASS | pytest; cross-backend interop 23/23 (last run 2026-09-25); browser login |

## Authorization

| Item | Status | Evidence |
|---|---|---|
| Server-side roles + ownership | PASS | C# and Python tests; chatbot personal answers only for the token's own user (tests: other users/roles get the generic reply) |
| Role permissions exercised in the browser | PARTIAL | citizen role only this round |

## QR

| Item | Status | Evidence |
|---|---|---|
| Signed QR generation and verification, masked details | PASS | C# `QrServiceTests`, `QrScanServiceTests` |
| Camera scanning | NOT TESTED | camera blocked in the test browser |

## OTP

| Item | Status | Evidence |
|---|---|---|
| OTP fallback (hashed, 5 min, 3 attempts, cooldown) | PASS | C# `SyntheticOtpServiceTests`, `OtpDeliveryTests` (no dedicated test for reusing a verified code) |
| Real SMS delivery | BLOCKED | needs a DLT-registered SMS gateway (adapter exists) |

## Appointments

| Item | Status | Evidence |
|---|---|---|
| 5-minute slots, capacity, booking, cancel | PASS | C# tests; MySQL concurrency test (30 racers, capacity 2 → exactly 2); live booking created and cancelled through the proxy |

## Inventory

| Item | Status | Evidence |
|---|---|---|
| Ledger, transactional collection, idempotency | PASS | C# `InventoryLedgerAndIdempotencyTests`, `RationCollectionServiceTests` |
| Inventory screens | NOT TESTED | this round |

## Synthetic Data

| Item | Status | Evidence |
|---|---|---|
| `DATA_MODE=synthetic` default; providers behind interfaces | PASS | tests (C# + Python) |
| Reference data in `database/seeds` (marked `isSynthetic`) | PASS | seed output identical to before; image-layout simulation |
| Every generated record tagged `SYNTHETIC_DEMO`, masked Aadhaar only | PASS | MySQL suite integrity tests |
| Central seeded generator (`app/synthetic`, `generate_test_data.py --users N --seed S`) | PASS | 23 unit tests; 1000 citizens inserted into `smartration_test` |
| Demo mobiles in the reserved `9000000xxx` block (were `9876543210–12`) | PASS | seeders, tests, dev DB rows updated |

## Real Data Architecture

| Item | Status | Evidence |
|---|---|---|
| Interfaces, `RealDataProvider`, startup refusal, migration checklist | PASS | tests; `database/seeds/REAL_DATA.md` |
| Real ration-card registry, eKYC, SMS, reference data | BLOCKED | REQUIRES EXTERNAL INTEGRATION (and legal/privacy review) |

## AI

| Item | Status | Evidence |
|---|---|---|
| Analytics service (forecasts, risk, alerts, OCR) | PASS | 46 tests; running and healthy |
| Trained ML models | NOT TESTED | none exist (statistical methods by design) |
| Generative LLM | BLOCKED | no provider or key; interface + prompt template ready |

## Chatbot

| Item | Status | Evidence |
|---|---|---|
| Floating assistant (quick questions, typing, history, search, clear, minimize, expand, offline, errors) | PASS | 18 component tests; browser |
| Knowledge retrieval en/hi/mr | PASS | evaluation 48/48 retrieval, 19/19 safety |
| Privacy: no personal data in public chat; signed-in citizen sees own booking | PASS | API tests; browser (Hindi, own token SR-2026-010088) |
| "Not able to verify" fallback, health guidance, refusal of internals | PASS | tests |

## Localization

| Item | Status | Evidence |
|---|---|---|
| en / hi / mr dictionaries complete | PASS | i18n tests |
| Public pages, chatbot, login, navigation translated | PASS | browser in all three languages |
| 41 older dashboard components | PARTIAL | still contain English text |

## Testing

| Suite | Result |
|---|---|
| Python 221 · MySQL 146 · root MySQL 24 · evaluation 67 · AI 46 · C# 130 (`SmartRation.sln`) · frontend 45 + ESLint (0 errors) + build · database health · E2E 9 | PASS (`run-tests.ps1 -MySql -E2E`, exit 0, 11/11 steps, 688 tests, 2026-09-26) |
| Fresh clone (no venvs, packages or `.env`): `setup.ps1`, then Python/AI/C#/frontend lint, tests, build | PASS (192 Python — the 3 live-MySQL schema tests skip without a database — 46 AI, 94 C#, 39 frontend, build) |
| Contract (proxy 36/36, auth interop 23/23) | PASS (earlier today; needs both servers) |
| E2E | PASS (9 Playwright tests, local; not in CI — it needs the whole stack running) |
| HTTP load: 10 / 100 / 1000 concurrent citizens through the gateway (`sr.ps1 load`) | PASS, 0 failures (2026-09-26, one machine); p95 53 ms / 463 ms / 8.7 s — see [LOAD_TESTING.md](testing/LOAD_TESTING.md) |
| Accessibility tooling | NOT TESTED |

## Security

| Item | Status |
|---|---|
| SQL injection, XSS in chat, secrets out of source, rate limits, no secrets in logs, masked Aadhaar | PASS |
| Refresh token in `localStorage` | PARTIAL — open (HIGH) |
| JWT key in old git history | PARTIAL — rotate before any public deployment |

## Documentation

| Item | Status |
|---|---|
| README (what/how/stack/architecture/flows/run/test/deploy), docs index, 6 architecture docs, LOCAL_SETUP, folder READMEs, `.env.example` | PASS — 57+ files, 0 broken links |
| VS Code workspace, tasks, launch configs ("Smart Ration: …") | PARTIAL — all 7 files parse, every reference/path checked; the .NET and Python launch commands and the Setup/Full Stack/Health Check/Tests/Database Health/Lint tasks were run from a terminal; the VS Code UI itself was not opened by me |

## Deployment

| Item | Status |
|---|---|
| Dockerfile (repo-root context, allow-list) | PASS — built locally (316 MB), container healthy, non-root (uid 10001), no `.env` inside, knowledge + reference data present, `/health` `/docs` 200 |
| docker-compose.yml | PARTIAL — `docker compose config` valid (refuses to run without secrets, as intended); not started (it would clash with the local MySQL :3306 and another project's container on :8000) |
| GitHub Actions CI | NOT TESTED — branch not pushed |
| nginx example | NOT TESTED |
| Scripts: setup (.ps1/.sh), start-all, stop-all, health-check, seed, run-tests | PASS — all run from a subfolder too; start-all failure report forced and seen; stop-all parse-checked only (it would stop your servers); setup.sh dry-run only (Git Bash) |

## Remaining issues

1. Root `.env` `DB_PASSWORD` is wrong (your action).
2. Push the branch so CI runs (now also the MySQL suite, the AI service tests, ESLint and the solution build).
3. Refresh token → HttpOnly cookie; rotate the JWT key before public use.
4. Complaints module (not implemented anywhere).
5. Translate the 41 older dashboard components; run the E2E suite in CI (needs the full stack in a job).
6. Rehearse a database restore; containerise the C# API if Docker becomes the deployment path.
7. Real-data integrations — BLOCKED, REQUIRES EXTERNAL INTEGRATION.
8. `mobile/` is still the Expo starter template (its README now says so); the planned features are not built.
9. Another project's Docker containers (`smart-ration-hsd2c-dashboard`: API on :8000, Postgres on :5432) share port 8000; this project now uses `127.0.0.1` URLs and `health-check.ps1` warns, but stop them to avoid confusion.
10. Reusing an already-verified OTP has no dedicated test (C#).
