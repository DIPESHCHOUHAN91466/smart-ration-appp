# Smart Ration HSD2C — Project Status

Date: 2026-09-25 · Branch `feature/python-backend-migration` (not pushed) · Audit: [PROJECT_AUDIT.md](PROJECT_AUDIT.md)

**PASS** = verified by automated tests and/or in the browser during this work · **PARTIAL** = works but
incomplete or only partly verified · **FAIL** = broken · **NOT TESTED** = not verified ·
**BLOCKED** = requires an external integration that doesn't exist.

## Frontend

| Item | Status | Evidence |
|---|---|---|
| Production build | PASS | `npm run build` (main bundle ≈ 520 KB, above Vite's 500 KB advisory) |
| Component tests | PASS | Vitest 36/36 |
| Landing page, Public Help, status page | PASS | browser (desktop + 375 px; en/hi/mr); tests |
| Citizen dashboard via the Python API | PASS | browser: login → dashboard, all calls 200, no console errors |
| Shop and government screens | PARTIAL | APIs 200 through the proxy (parity 36/36); screens not re-checked visually this round |
| Layout kept, every folder documented | PASS | READMEs in `frontend/`, `src/*`, `tests/` |
| TypeScript | NOT TESTED | not used (JavaScript app) |
| End-to-end browser automation | NOT TESTED | none exists |

## Backend (C# business API)

| Item | Status | Evidence |
|---|---|---|
| Build + tests | PASS | xUnit 94/94 (8 new data-mode tests) |
| Business logic owner (frozen hybrid) | PASS | decision recorded; proxy parity 36/36 |
| Controllers thin, services + interfaces; no repository layer (by design) | PASS | documented in BACKEND_ARCHITECTURE.md |
| Data-mode guard | PASS | real mode refused at startup (verified by running the API with `DATA_MODE=real`) |

## Python

| Item | Status | Evidence |
|---|---|---|
| Python API (gateway, auth, chatbot, data providers, migrations) | PASS | pytest 164/164; ruff + mypy clean |
| AI service | PASS | pytest 46/46; `/health` 200 |
| Package structure, type hints, config via environment | PASS | see PYTHON_ARCHITECTURE.md |

## MySQL

| Item | Status | Evidence |
|---|---|---|
| `smartration`: 25 tables, Alembic `0001_initial`, 0 drift | PASS | `verify_database.py` |
| MySQL suite on `smartration_test` (CRUD, injection, performance, concurrency, errors, integrity) | PASS | 123/123 via `run-tests.ps1 -MySql` |
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
| OTP fallback (hashed, 5 min, 3 attempts, cooldown) | PASS | C# `OtpDeliveryTests` |
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
| Reference data in `data/synthetic` (marked `isSynthetic`) | PASS | seed output identical to before; image-layout simulation |
| Every generated record tagged `SYNTHETIC_DEMO`, masked Aadhaar only | PASS | MySQL suite integrity tests |

## Real Data Architecture

| Item | Status | Evidence |
|---|---|---|
| Interfaces, `RealDataProvider`, startup refusal, migration checklist | PASS | tests; `data/real/README.md` |
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
| Python 164 · MySQL 123 · evaluation 67 · AI 46 · C# 94 · frontend 36 | PASS (`run-tests.ps1 -MySql`, exit 0) |
| Contract (proxy 36/36, auth interop 23/23) | PASS (earlier today; needs both servers) |
| E2E, load, accessibility tooling | NOT TESTED |

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
| VS Code workspace, tasks, launch configs | PARTIAL — JSON validated, scripts run; not opened in VS Code by me |

## Deployment

| Item | Status |
|---|---|
| Dockerfile / compose (repo-root context, allow-list) | NOT TESTED — Docker engine unavailable here; image layout simulated; CI builds it |
| GitHub Actions CI | NOT TESTED — branch not pushed |
| nginx example | NOT TESTED |
| Scripts: start-all, stop-all, health-check, seed, run-tests | PASS (stop-all: parse-checked only, not run — it would stop your servers) |

## Remaining issues

1. Root `.env` `DB_PASSWORD` is wrong (your action).
2. Push the branch so CI runs (includes the Docker build).
3. Refresh token → HttpOnly cookie; rotate the JWT key before public use.
4. Complaints module (not implemented anywhere).
5. Translate the 41 older dashboard components; E2E tests (Playwright).
6. Rehearse a database restore; containerise the C# API if Docker becomes the deployment path.
7. Real-data integrations — BLOCKED, REQUIRES EXTERNAL INTEGRATION.
8. `tests/DROP DATABASE IF EXISTS smart_ratio.txt` (your notes) is untracked.
