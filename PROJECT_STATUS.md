# Smart Ration HSD2C — Project Status

Date: 2026-09-25 · Branch `feature/python-backend-migration` (not yet pushed) · Audit: [PROJECT_AUDIT.md](PROJECT_AUDIT.md)

**Legend** — PASS: verified by automated tests and/or a browser check in this work ·
PARTIAL: works but incomplete, or only partly verified · FAIL: known broken ·
NOT TESTED: not verified in this work.

## Existing Features

| Feature | Status | Evidence / note |
|---|---|---|
| Registration, login, logout, token refresh | PASS | Python tests; 23/23 cross-backend interop; browser login as citizen |
| Backend role-based authorisation | PASS | route role checks + ownership in services; C# + Python tests |
| Rural user dashboard | PASS | browser: loads through the Python proxy, API calls 200, no console errors |
| Ration shop dashboard, queue | PARTIAL | APIs pass proxy parity (36/36); screens not re-checked in the browser this release |
| QR scanner (camera) | NOT TESTED | the browser pane blocks the camera; scan/verify logic covered by C# tests |
| Government dashboard, statistics, reports, map, AI centre | PARTIAL | APIs return 200 through the proxy; screens not re-checked visually |
| Admin dashboard | PARTIAL | Admin uses the government screens; no separate admin UI |
| Ration-card management | PARTIAL | card data is modelled via family + passbook (read-only in the app); issuing/changing cards is a state process (documented in Public Help) |
| Family members | PARTIAL | view with eligibility: PASS; add/remove members in-app: not implemented |
| Aadhaar verification (simulated, masked) | PASS | synthetic `XXXX-XXXX-####` only; MySQL suite checks no real identifiers |
| Passbook verification | PASS | C# tests |
| QR verification (signed tokens) | PASS | C# `QrServiceTests`, `QrScanServiceTests` |
| OTP fallback (mock SMS mode) | PASS | C# `OtpDeliveryTests`; hashed OTPs, 5 min / 3 attempts |
| Token generation, 5-minute slots, capacity | PASS | C# tests; MySQL suite: 30 concurrent bookings on capacity 2 → exactly 2 |
| Item selection, entitlement calculation | PASS | C# `EntitlementServiceTests` |
| Inventory + ledger | PASS | C# `InventoryLedgerAndIdempotencyTests` |
| Collection tracking (transactional, idempotent) | PASS | C# `RationCollectionServiceTests`, `CollectionSecurityTests` |
| Transaction / booking history | PARTIAL | exists; not re-verified in this release |
| Notifications | PASS | browser: API 200 through the proxy |
| Reports, search, filtering, pagination | NOT TESTED | exist in the C# API; not exercised in this release |
| Audit logs | PARTIAL | written by C# and Python services; audit screen not re-checked |
| Language switching | PARTIAL | complete for public pages, chatbot, login, sidebar; 41 of 53 older dashboard components still have English text |
| Responsive UI | PARTIAL | public pages + chatbot verified at 375 px; dashboards not re-checked |

## Newly Added Features

| Feature | Status | Evidence |
|---|---|---|
| Public landing page (`/`) | PASS | browser (desktop, 375 px, en/hi/mr); 5 component tests |
| Public Help page (`/help`): categories, articles, search | PASS | browser (mr, mobile); 4 component tests; API tests |
| Smart Ration AI Assistant (floating chatbot) | PASS | browser: quick questions, typed questions, privacy reply, live shop list, Hindi; 17 component + 82 backend tests |
| Chatbot branding (logo/avatar/icon SVG from the Ration Mitra mark) | PASS | rendered in the browser |
| Public user role (anonymous access to landing, help, chatbot) | PASS | routes need no login; API ignores Authorization |
| Chatbot/help content in en, hi, mr | PASS | integrity tests fail on any missing translation |
| Frontend test runner (Vitest) | PASS | 33 tests; added to CI |
| Root `tests/mysql` suite | PARTIAL | 24/24 pass with the correct password; the root `.env` `DB_PASSWORD` is wrong (tests error clearly) |
| nginx reverse-proxy example | NOT TESTED | configuration example only |
| Generative LLM behind the chatbot | NOT IMPLEMENTED | by design (no provider/key); interface ready (docs/CHATBOT.md) |
| Complaints workflow | NOT IMPLEMENTED | Public Help explains the official complaint channels |
| Microphone input | NOT IMPLEMENTED | intentionally omitted (not supported end to end) |

## Fixed Features

| Problem | Status | Evidence |
|---|---|---|
| Concurrent registrations deadlocked (35/100 → HTTP 500), both backends | PASS | 100 simultaneous registrations now succeed (MySQL suite); C# tests 86/86 |
| 500 responses without `X-Request-ID`; error logs without request id | PASS | MySQL suite error-handling test |
| pytest collection broken (relative imports; ignored root setting) | PASS | collects from each backend and from the repository root |
| C# per-IP rate limits saw all proxied traffic as 127.0.0.1 | PARTIAL | forwarded headers enabled; build + proxy parity pass; not verified with two real client IPs |
| Chatbot formatting with repeated blank lines; shop search matched all names | PASS | regression tests |
| API docs described validation errors wrongly | PASS | corrected |

## Database Status

| Item | Status |
|---|---|
| `smartration` (MySQL 8.0.46): 25 tables, 24 FKs, 37 indexes, Alembic `0001_initial`, 0 drift | PASS (`verify_database.py`) |
| `smartration_test`: application schema + your `test_users` table | PASS |
| MySQL suite (CRUD, injection, performance, concurrency, errors, integrity) | PASS — 122/122 |
| Backup | PASS (tested 2026-09-24) |
| Restore | NOT TESTED (needs a root-created scratch database) |
| Brief entities without tables (complaints, chatbot_faq, public_help_content, permissions) | not created — help content lives in versioned JSON; see PROJECT_AUDIT.md §6 |

## Backend Status

| Component | Status |
|---|---|
| Python FastAPI (auth, health, public help, chatbot; proxy for the rest) | PASS — 136 tests, ruff + mypy clean |
| C# ASP.NET Core API (all other routes) | PASS — 86 tests |
| AI service | PASS — 46 tests |
| Proxy parity C# vs Python | PASS — 36/36 |

## Frontend Status

| Item | Status |
|---|---|
| Production build | PASS (main bundle 519 KB, above Vite's 500 KB advisory; mostly translations) |
| Calls the Python backend (`:8000`) | PASS — every request 200 in the browser, no console errors |
| Component tests | PASS — 33/33 |
| End-to-end browser automation | NOT TESTED — none exists |

## Chatbot Status

PASS — retrieval assistant over 25 reviewed articles (12 categories), safety rules (sensitive input,
internals, private data, health), live public data, rate-limited, message text never logged, text-only
rendering, en/hi/mr, mobile bottom sheet, keyboard and screen-reader support. Not an LLM.

## Localization Status

PARTIAL — English, Hindi and Marathi dictionaries are complete (355 + 120 keys, no gaps); the public
pages, chatbot, login and navigation are fully translated; 41 older dashboard components still contain
hard-coded English.

## Testing Status

| Suite | Result |
|---|---|
| Python backend | 136 passed |
| MySQL suite on `smartration_test` | 122 passed |
| Root `tests/mysql` | 24 passed with correct credentials |
| AI service | 46 passed |
| C# | 86 passed |
| Frontend | 33 passed |
| Contract (proxy / auth interop) | 36/36 · 23/23 (last run 2026-09-25) |
| E2E, load, accessibility audit tools | NOT TESTED |

## Security Status

| Item | Status |
|---|---|
| SQL injection | PASS (16 payloads, bound parameters everywhere) |
| XSS in chatbot/help | PASS (text-only rendering, no `dangerouslySetInnerHTML` anywhere) |
| Secrets out of source; `.env` ignored | PASS |
| Aadhaar / OTP / password never logged or exposed by the chatbot | PASS |
| Rate limiting (auth, chatbot, help, QR scan, OTP) | PASS |
| Tokens in `localStorage` | PARTIAL — open (HIGH): move the refresh token to an HttpOnly cookie |
| JWT key present in old git history | PARTIAL — open (HIGH): rotate before public deployment |

## Deployment Status

| Item | Status |
|---|---|
| Dockerfile, docker-compose | NOT TESTED (Docker engine unavailable on this machine) |
| GitHub Actions CI | NOT TESTED (branch not pushed; runs on push) |
| Health endpoints `/health`, `/ready`, `/api/health` | PASS |
| nginx example | NOT TESTED |

## Remaining Issues

1. **Your action:** set `DB_PASSWORD` in the root `.env` to the `smartration_app` password (the same as
   in `backend/SmartRation.Python/.env`), so `tests/mysql` runs.
2. Push the branch so CI runs (Docker build included); Docker still unverified locally.
3. Refresh token → HttpOnly cookie; rotate the JWT key before any public deployment.
4. Translate the remaining 41 dashboard components; responsive check of dashboards.
5. Add end-to-end tests (Playwright) for login → book → QR → collect.
6. Rehearse a database restore.
7. Complaints module; in-app family changes (if wanted).
8. Continue the C# → Python migration (users, items, slots next) and merge the AI service.
9. Main bundle > 500 KB: lazy-load the chatbot window / split translations.
10. `tests/DROP DATABASE IF EXISTS smart_ratio.txt` (your SQL notes) is untracked; keep or delete as you prefer.
