# Smart Ration HSD2C — Project Audit

Latest: third audit, 2026-09-26 (below) · First audits: 2026-09-25 · Previous audits:
[docs/archive/PROJECT_AUDIT_2026-09-21.md](archive/PROJECT_AUDIT_2026-09-21.md) (pre-cleanup state, now outdated) and
[MIGRATION_AUDIT.md](migration/MIGRATION_AUDIT.md) (C# → Python migration, Phase 0).

Everything below was checked against the code, the running services and the database on this date;
items marked *fixed* were fixed during this audit and committed.

## Third audit — after the move to `D:\` (2026-09-26)

Triggered by the "Super Master Prompt" brief. The project was moved from
`C:\Users\…\Desktop\Smart_Ration_HSD2C_Final` to `D:\Smart_Ration_HSD2C_Final` (same git history,
`main` at `75ae91c`, 2 commits not yet pushed).

### Baseline in the new location (measured, not assumed)

| Check | Result |
|---|---|
| `health-check.ps1 -SkipServices` | HEALTHY — every script finds the project from its own location |
| `run-tests.ps1 -MySql` | 9/9 steps PASS: Python 208, MySQL 146, AI 46, C# 114, frontend 39, chatbot evaluation 67/67, lint, build, database health |
| Python virtualenvs | **broken by the move**: `pytest.exe`, `uvicorn.exe`, `activate` pointed to the old `C:` path (only `python -m …` worked) — **fixed**: `setup.ps1` now detects a moved `.venv` and rebuilds it; `health-check.ps1` warns (`scripts/development/_common.ps1`) |
| Absolute paths in tracked files | none in code; 2 in docs (**fixed**) |
| Root `tests/mysql` (24) | still 23 errors: *Access denied* — the root `.env` `DB_PASSWORD` is wrong, and this suite keeps its **own** DB settings (`DB_*`) instead of the project's `DATABASE_URL` (a duplicate configuration system) |

### Dependency security (first time checked)

| Stack | Tool | Result |
|---|---|---|
| Python API, AI service | `pip-audit` (scratch venv) | no known vulnerabilities |
| Frontend, production deps | `npm audit --omit=dev` | 0 |
| Frontend, dev deps | `npm audit` | 2 moderate (Vitest's `@vitest/mocker`; test tooling only; fix needs a Vitest major upgrade) |
| C# API (**ships in the production image**) | `dotnet list package --vulnerable --include-transitive` | **3 high**, transitive: `Microsoft.Extensions.Caching.Memory 8.0.0`, `System.Text.Json 8.0.4`, `SQLitePCLRaw.lib.e_sqlite3 2.1.6` (via EF Core / JwtBearer 8.0.8, EF Sqlite) |
| C# tests | same | the 3 above + `System.Net.Http 4.3.0`, `System.Text.RegularExpressions 4.3.0` |

### Architecture findings

- **13 of 25 C# controllers still query the database directly** (`AI`, `Admin`, `Audit`, `Families`,
  `Health`, `Public`, `RationCollection`, `Ration`, `Search`, `Shops`, `SyntheticData`, `Users`,
  `Verification`). Health's connectivity probe is legitimate; the rest is the same layering debt fixed for
  `Beneficiaries`/`AdminDatabase` in the previous round.
  **Fixed (2026-09-26):** 12 controllers now call services (`UserAccountService`, `FamilyService`,
  `PublicProfileService`, `ShopDirectoryService`, `RationCatalogService`, `SearchService`, plus new methods
  on the verification-audit, OTP, beneficiary-profile and database-browser services); only `Health` keeps
  its DbContext, on purpose. One access rule (`BeneficiaryAccess`) replaces four copies; the synthetic-data
  list reuses the database viewer's query. Found and fixed on the way: a profile update with a
  space-padded duplicate mobile number returned 500 instead of 409. C# tests 114 → 130; 22 endpoint
  checks (including every 403 boundary) passed against the running API and local MySQL.
- **Open decision (not changed):** a ShopOwner can open *any* beneficiary's profile, family and history
  (`BeneficiaryAccess`), while search limits them to their own shop's. Which one is intended is the owner's call.
- **Missing feature:** `GET/PUT /api/users/profile` (edit own name + mobile) exists in the C# API, and
  `frontend/src/services/usersService.js` wraps it, but **no page uses it** — the only unimported frontend
  file. Classification MODIFY (build the screen), not DELETE.
- No API versioning (`/api/...`, no `/api/v1`).
- Python: clean layering (`api → services → db`), lint + types clean, 45 source files.

### Why C# stays (the brief's Python-first rule, §7)

| Question | Answer |
|---|---|
| What does it do? | the business core: bookings + 5-minute slots, QR signing/verification, OTP, entitlement, collections, inventory ledger, AI panels' data, 75 endpoints, 130 tests |
| Why not Python? | it isn't *better* in Python, it's already built and tested there; porting 75 endpoints means re-deriving concurrency rules (optimistic concurrency on slots and stock), QR signatures and EF migrations, with regression risk and no user-visible gain. The owner chose "freeze as hybrid" on 2026-09-25 |
| How does it integrate? | only through the Python gateway (`LEGACY_API_URL`), same MySQL, same JWT key; the browser never calls it directly |
| When would it move? | per route area, behind the existing proxy, when its tests and the contract check (`tests/contract/compare_proxy.py`) pass — see `backend/SmartRation.Python/MIGRATION.md` |

### Classification of important paths

| Path | Type | Purpose | Status | Recommendation | Reason / risk |
|---|---|---|---|---|---|
| `frontend/` | React 18 + Vite (JS) | web app | working, 39 tests, 9 E2E | KEEP | TypeScript would be a rewrite of ~130 files; no defect requires it |
| `frontend/src/services/usersService.js` | API client | own-profile API | unused | MODIFY | build the missing "My profile" screen |
| `backend/SmartRation.Python/` | FastAPI | gateway, auth, chatbot, website serving, data tools | working, 208 tests | KEEP | primary backend (Python-first) |
| `backend/SmartRation.Api/` | ASP.NET Core 8 | business core | working, 130 tests | KEEP + MODIFY (done) | justified above; DB access moved out of 12 controllers; vulnerable packages patched |
| `backend/SmartRation.Api/Repositories/`, `Validators/` | empty folders (untracked) | none | empty | DELETE | nothing references them; empty folders mislead |
| `backend/SmartRation.AI/` | FastAPI | forecasting, risk, alerts, OCR | working, 46 tests | KEEP | isolated, fails gracefully (panels show "unavailable") |
| `backend/SmartRation.Python/MIGRATION.md` | doc | paused migration tracker | referenced by `app/main.py`, READMEs | KEEP | historical record of the hybrid decision |
| `ai/`, `data/`, `database/`, `api/` | content | knowledge base, synthetic data, schema snapshot, API contracts | current, drift-tested | KEEP | — |
| `tests/mysql/` | pytest | root MySQL tests (24) | broken (config) | MODIFY | use the project's `DATABASE_URL`/`TEST_DATABASE_URL`, drop the duplicate `DB_*` settings |
| `mobile/` | Expo template | planned mobile app | not integrated | KEEP (marked planned) | owner's decision; README states it's a template |
| `scripts/start-backend.ps1`, `start-frontend.ps1` | PowerShell | start one service | work, relative paths | KEEP | small, documented; `sr.ps1 run` / VS Code tasks are the main path |
| `start-dev.bat`, `sr.ps1` | entry points | double-click start; one CLI | working | KEEP | — |
| `docs/archive/` | docs | superseded audits | historical | KEEP | clearly labelled archive |
| `DATABASE_TESTING_COMPLETION_REPORT.md` | report | database testing results | current | KEEP | requested at the root by an earlier brief |
| `render.yaml`, both `Dockerfile`s | deployment | Render blueprint, images | verified locally | KEEP | Render itself NOT VERIFIED (needs the owner's accounts) |

### Brief's target structure vs. what exists

The brief's tree is a *target*, not an instruction to create empty folders. Where a folder it names has an
existing equivalent, that equivalent is kept:

| Brief | Existing equivalent |
|---|---|
| `backend/SmartRation/app/{api,core,config,models,schemas,services,database,security,middleware}` | `backend/SmartRation.Python/app/{api,core,db,schemas,services,…}` (config/security/middleware live in `app/core`) |
| `app/repositories` | SQLAlchemy sessions used in services (no separate repository layer: 13 short services, no second data source) |
| `ai/{models,inference,evaluation,…}` | `backend/SmartRation.AI/smartration_ai/*` (service) + `ai/chatbot/{knowledge,evaluation,prompts}` |
| `database/{migrations,schema,seeds}` | Alembic in `backend/SmartRation.Python/app/db/migrations`, `database/schema/`, `data/synthetic` |
| `tests/{e2e,smoke,…}` | `frontend/e2e` (Playwright), `tests/mysql`, per-service `tests/` folders |
| root `ARCHITECTURE.md`, `TESTING.md`, `DEPLOYMENT.md`, `DEVELOPMENT.md` | `docs/architecture/`, `docs/testing/TESTING.md`, `docs/deployment/`, `docs/development/LOCAL_SETUP.md` |

## 0. Second audit — workspace, data separation, documentation (2026-09-25, later)

Triggered by the "professional architecture + VS Code" brief. Decisions taken with the owner:
**frozen hybrid** backend (C# = business logic; Python = gateway, auth, chatbot, AI, data; migration
paused) and **keep the frontend folder layout** (document, don't rename).

| Finding | Priority | Status |
|---|---|---|
| `Demo:UseSyntheticAadhaar/Passbook` flags were never read — synthetic providers registered unconditionally (a "fake switch") | HIGH | **fixed**: `DATA_MODE` + `DataModeGuard`; real mode / flags off → startup refused, *BLOCKED — REQUIRES EXTERNAL INTEGRATION* |
| Python registration fabricated synthetic identity records inline | MEDIUM | **fixed**: `app/data_providers` (`SyntheticDataProvider` / `RealDataProvider`) |
| No `data/` separation; seed reference data hard-coded in a script | MEDIUM | **fixed**: `data/synthetic/reference/*.json` (marked `isSynthetic`), seed output verified identical |
| Chatbot knowledge inside backend code; no evaluation set | MEDIUM | **fixed**: `ai/chatbot/knowledge`, `ai/chatbot/evaluation` (67 cases, 100%), evaluator command |
| Logged-in users couldn't ask the chatbot about their own appointment | MEDIUM | **added**: own bookings only, from the verified token's user id |
| `start-dev.bat` didn't start the Python API although the frontend calls it (Network Error) | HIGH | **fixed**: delegates to `scripts/development/start-all.ps1` |
| `scripts/start-backend.ps1` / `start-frontend.ps1` used paths from the drive root | LOW | **fixed** |
| `.vscode/launch.json` empty; no workspace map | LOW | **fixed**: launch configs + Full Stack compound, 22 tasks, numbered `.code-workspace` |
| README described the old mock-data prototype (PostgreSQL); `database/README.md` said EF owns the schema | MEDIUM | **fixed** (old text archived in `docs/archive`) |
| No README in frontend, backend, AI service, database/mysql, ai, data, tests, scripts, deployment | MEDIUM | **fixed** (each answers what / why / belongs / doesn't / run / connects) |
| Docs flat in `docs/` | LOW | **fixed**: `docs/{architecture,api,database,chatbot,security,testing,deployment,development,migration}`; 0 broken links |
| `/health` didn't show the AI service or data mode; no status page | LOW | **fixed**: `aiService`, `chatbot`, `dataMode`; `/status` (dev) |
| Docker image couldn't include `ai/` and `data/` | MEDIUM | **fixed**: repo-root build context + allow-list `.dockerignore` (image itself still built only in CI) |
| `run-tests -MySql` silently skipped the MySQL suite; C# tests failed while the API ran | MEDIUM | **fixed** |
| C# has no repository layer | — | **kept by design** (EF `DbContext` is the repository; documented in BACKEND_ARCHITECTURE.md) |
| Frontend is JavaScript, not TypeScript | — | kept (conversion possible later, file by file) |
| Complaints module, E2E tests, TypeScript, 41 untranslated dashboard components, tokens in localStorage, JWT key in git history, bundle > 500 KB, Docker unverified locally, CI not yet run, root `.env` DB password wrong, mobile app is a template | — | **open** — see PROJECT_STATUS.md |

## 1. Current architecture (first audit, same day)

```
Browser ── React 18 / Vite 6 SPA (:5173)
              │  VITE_API_BASE_URL = http://localhost:5188/api   ← still calls C# directly
              ▼
        ASP.NET Core 8 API (:5188) ──── EF Core 8 (Pomelo) ──┐
              │ HTTP (AI analytics)                           │
              ▼                                               ▼
        Python AI service (:8001) ────────────────────► MySQL 8 `smartration`
                                                              ▲   (25 tables, owned by Alembic)
        Python FastAPI backend (:8000) ── SQLAlchemy 2 ───────┘
              serves /health /ready /api/auth/*, proxies every other /api/* to C#
```

| Path | What it is | State |
|---|---|---|
| `frontend/` | React 18, Vite 6, react-router 7, zustand, axios, zod, lucide, html5-qrcode, leaflet, qrcode | builds; 53 components/pages; no test runner |
| `backend/SmartRation.Api/` | ASP.NET Core 8, 25 controllers, 81 endpoints | builds; 86 xUnit tests pass |
| `backend/SmartRation.Python/` | FastAPI replacement (side-by-side, fallback proxy) | auth + health migrated; 54 unit + 122 MySQL tests pass |
| `backend/SmartRation.AI/` | FastAPI AI/analytics service (to be merged into the Python backend) | 46 tests pass |
| `mobile/` | Expo 57 default template | not integrated with the API |
| `database/mysql/` | backup/restore scripts | backup tested; restore not rehearsed |
| `tests/mysql/` | root-level MySQL tests on `smartration_test` | 24 tests (need correct root `.env`) |
| `docs/` | architecture, database, migration, API, security, deployment, backup, testing guide… | current |
| `.github/workflows/ci.yml`, `docker-compose.yml`, `deployment/docker/` | CI + containers | written; not yet run (branch not pushed; Docker engine unavailable locally) |

## 2. Existing features (verified)

| Feature | Where | Status |
|---|---|---|
| Register / login / refresh / logout | Python `/api/auth` (C# too) | works; Argon2id, BCrypt upgraded on login |
| Roles: RuralUser, ShopOwner, GovernmentOfficial, Admin | backend-enforced (`[Authorize]`, `require_roles`) + route guards | works |
| Rural dashboard, booking, 5-minute slots (capacity 2), token, booking history | `pages/rural/*` + C# | works |
| QR tokens (HMAC-signed `SRQR-…`), shop scanner (camera, image, manual), OTP fallback (mock SMS) | `components/qr`, `components/verification`, C# | works (camera needs a real browser) |
| Entitlement calculation per scheme, family members, masked Aadhaar, passbook | C# services, `BeneficiaryProfile` | works; synthetic data only |
| Collection (transactional, idempotent), inventory ledger | C# | works |
| Notifications, audit log, search | C# + pages | works |
| Government: dashboard, statistics, reports, bookings, shops, users, inventory, map, AI center, synthetic data, DB viewer | `pages/government/*` | works |
| AI alerts, forecasts, OCR (optional Tesseract) | AI service + C# | works |
| Languages en / hi / mr | `i18n/translations.js` (355 keys × 3, complete) | **partial**: only 12 of 53 components use it |
| Health | `/api/health` (C#), `/health`, `/ready` (Python) | works |

## 3. Missing features

| Item | Priority | Plan |
|---|---|---|
| Public landing page (`/` redirects straight to login) | HIGH | add |
| Public Help section (searchable, no login) | HIGH | add (Python `/api/public-help`) |
| Public Help AI Chatbot (bottom-right) | HIGH | add (Python `/api/chatbot`, retrieval over a curated knowledge base; LLM-ready interface) |
| "Public user" role | MEDIUM | = anonymous access to landing, help and chatbot; no account needed |
| Frontend tests (none exist) | HIGH | add Vitest + Testing Library |
| i18n in the 41 components still hard-coded in English | MEDIUM | new UI fully translated; existing dashboards converted over time |
| Complaints / grievance workflow | MEDIUM | not present in any layer; documented as future work |
| Separate admin UI (Admin shares government screens) | LOW | keep; document |
| Ration-card entity (passbook plays this role) | LOW | documented mapping in docs/database/DATABASE_ARCHITECTURE.md |
| Payments | — | not a feature of this system (decision recorded) |
| `CONTRIBUTING.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`, `docs/chatbot/CHATBOT_ARCHITECTURE.md`, `docs/testing/TESTING.md`, root `SECURITY.md` | MEDIUM | add |
| `deployment/nginx`, `deployment/cloud` content | LOW | add reverse-proxy example |

## 4. Broken or weak (found in this audit)

| Problem | Priority | Status |
|---|---|---|
| pytest collection broken after `tests/__init__.py` removal (relative imports; root `import_mode` key silently ignored) | CRITICAL | **fixed** (`4491b6c`) — collects from each backend and from the root |
| Concurrent registrations deadlock (35/100 → HTTP 500): placeholder code `""` on UNIQUE columns, in **both** backends | HIGH | **fixed** (`4491b6c`, `53f6080`) |
| 500 responses lacked `X-Request-ID`; error log had `request_id "-"` | MEDIUM | **fixed** (`4491b6c`) |
| C# per-IP rate limiter saw every proxied request as 127.0.0.1 | MEDIUM | **fixed** (`53f6080`, forwarded headers from loopback only) |
| Root `.env` `DB_PASSWORD` doesn't match the `smartration_app` account (error 1045) | MEDIUM | owner action: copy the password from `backend/SmartRation.Python/.env` |
| `docs/api/API.md` described validation errors as a map; they're a list | LOW | **fixed** |
| Frontend calls C# directly, bypassing the Python backend | MEDIUM | switch `VITE_API_BASE_URL` to :8000 (proxy parity 36/36 verified) |
| Old `PROJECT_AUDIT.md` described a state that no longer exists | LOW | archived |

## 5. Security

| Finding | Priority | Notes |
|---|---|---|
| Access **and refresh** tokens persisted in `localStorage` | HIGH | an XSS bug would expose them; move refresh token to an HttpOnly cookie (needs backend + CSRF work) — planned, not done |
| JWT key and QR secret in git history before `4c983e2` | HIGH | rotate JWT key before any public deployment; QR secret kept by owner decision (docs/security/SECURITY_ARCHITECTURE.md) |
| Demo password shown on the login page | MEDIUM | fine for the demo; hide via config in production |
| No `dangerouslySetInnerHTML`; React escapes output | ✓ | chatbot must keep rendering plain text |
| SQL injection | ✓ | bound parameters everywhere; 16 payloads tested (MySQL suite) |
| Rate limiting on auth, QR scan, OTP | ✓ | new public endpoints (chatbot) need their own limit |
| Secrets in `.env` / user-secrets only; `.env` git-ignored | ✓ | |
| Aadhaar only masked/synthetic; OTP hashed; logs without secrets | ✓ | verified by tests |

## 6. Database

`smartration` (MySQL 8.0.46): 25 tables, 24 FKs, 37 indexes, Alembic `0001_initial`, 0 drift,
utf8mb4, strict mode. `smartration_test`: application schema + the owner's `test_users` table.
Full 122-test MySQL suite passes (CRUD, injection, performance, concurrency, errors, integrity).
Brief entities without tables: `complaints`, `chatbot_faq`, `public_help_content`, `permissions`,
`shop_operators` (operators are `Users.RationShopId`). Chatbot/help content will live in versioned
JSON knowledge files first (reviewable in git); a table is only worth adding once it's edited in-app.

## 7. Testing

| Suite | Result |
|---|---|
| C# xUnit | 86 / 86 |
| Python backend unit | 54 / 54 |
| Python MySQL suite (`smartration_test`) | 122 / 122 |
| AI service | 46 / 46 |
| Root `tests/mysql` | 24 / 24 with correct credentials |
| Contract: proxy parity / auth interop | 36 / 36 · 23 / 23 |
| Frontend | build OK; **no tests** |
| E2E / browser automation | none |

## 8. Recommended implementation order (status after this work: see PROJECT_STATUS.md)

1. ✅ Fix test collection and the bugs the MySQL suite exposed.
2. ✅ Public Help + Chatbot backend (Python): knowledge base, search, rate limit, privacy guard, tests.
3. ✅ Frontend: route through the Python backend; landing page; Public Help page; chatbot widget +
   branding assets; all new UI in en/hi/mr.
4. ✅ Frontend test runner + chatbot/landing tests.
5. ✅ Browser verification on desktop and mobile widths; fix console errors.
6. ✅ Docs: `PROJECT_STATUS.md`, `docs/chatbot/CHATBOT_ARCHITECTURE.md`, `docs/testing/TESTING.md`, `CONTRIBUTING.md`,
   `CHANGELOG.md`, root `SECURITY.md`; nginx example.
7. Next: translate the remaining dashboards; refresh token → HttpOnly cookie; complaints module;
   continue the C# → Python migration (users, items, slots…).
