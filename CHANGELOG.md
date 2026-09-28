# Changelog

All notable changes. Dates are commit dates; hashes refer to this repository.

## 2026-09-28 — Target architecture: every folder with a purpose and real code

Moves were made with `git mv` (history kept); every phase was tested and committed separately
(0165b7b, 830bedf, 2c0dd2c, fdee2b3, 15393a8, 6418f25, 9851ff3).

### Changed (layout)
- `backend/SmartRation.Python` → `backend/SmartRation`; inside `app/`: `config/`, `security/`, `middleware/`,
  `api/{routes,dependencies}`, `database/`, `models/` (one module per domain), `ai/chatbot/`; Alembic → `migrations/`.
- AI service `backend/SmartRation.AI` → `ai/` (package `ai`) by stage: `configs`, `preprocessing`, `models`,
  `training`, `evaluation`, `inference`, `postprocessing`, `pipelines`, `api`.
- Frontend `src/`: `api/`, `config/env.js`, `state/` (was `store/` + toast context), `features/{qr,auth,chatbot}`,
  `styles/`, `utils/`, `types/`; `layouts/PublicLayout`.
- `data/` → `database/seeds/`; `api/openapi` → `docs/api/openapi`; scripts by purpose (`scripts/{development,database,
  testing,deployment}`); `docker-compose.yml` → `deployment/docker/` (now with the C# API).
- Tests by layer: gateway `tests/{unit,api,integration,security,performance}`; root `tests/{e2e,smoke,integration,regression}`
  (`frontend/e2e` became its own small Node project in `tests/e2e`).
- 18 empty scaffold folders removed; root `ARCHITECTURE.md`, `DEVELOPMENT.md`, `TESTING.md`, `DEPLOYMENT.md`.

### Added
- Gateway `repositories/` (all SQL out of the services), `utils/masking`, `workers/cleanup` (expired refresh tokens).
- `database/queries/` — 8 read-only integrity checks + `check_data_integrity.py` (CI `--strict`);
  `database/migrations/` — generated SQL per Alembic revision (drift-tested).
- AI: `MODEL_VERSION` on every forecast and in `/health`; `python -m ai.evaluation.report` (accuracy per shop and item).
- Deployment: `staging/` and `production/` env templates (tested against the settings the code reads) and checklists;
  `deployment/scripts/backup-mysql.sh`; `scripts/deployment/{build-images,verify-deployment}.ps1`; `tests/smoke`.
- Tests: security controls (17), latency budgets (3), repositories, worker, integrity, backup script, env templates,
  AI stages (12), frontend formatting (6), 21 cross-component contract tests; `docs/user-guides/` for each role.

### Fixed
- C# seeder counted cancelled demo tokens in `TimeSlots.BookedCount` (found by the new drift check).
- Times from the C# API (no `Z`) were shown 5 h 30 min early on My Token and Notifications.
- ESLint fast-refresh warnings (2 → 0).

## 2026-09-26 — Move to `D:\`, third audit, dependency security, C# cleanup, `/api/v1`

### Added
- **HTTP load test** (`sr.ps1 load`): 10 / 100 / 1000 concurrent citizens through the gateway, 0 failures;
  a rate-limit burst is answered with clean 429s. Method and results: `docs/testing/LOAD_TESTING.md`.
- **My profile** (Settings page, every role): edit your own name and mobile number; the email is shown
  read-only. English, Hindi and Marathi; 4 tests. Uses the existing `GET/PUT /api/v1/users/profile`.
- Disabled buttons now look disabled (before, "Save" / "Apply Language" looked clickable when they weren't).
- **API versioning:** every gateway route answers under `/api/v1/...`; `/api/...` stays as an alias
  (`app/core/api_version.py`, 11 tests). The frontend calls `/api/v1` (a bare `/api` base gets `/v1` added).
- Dependency audit: `sr.ps1 audit` (pip-audit, npm audit, `dotnet list package --vulnerable`) and a CI
  `security` job. CI's docker job checks the built website and that the C# image runs as non-root.
- Moved-virtualenv detection and repair in `setup.ps1` / `health-check.ps1`.

### Changed
- **C# API layering:** 12 controllers call services instead of the database (`UserAccountService`,
  `FamilyService`, `PublicProfileService`, `ShopDirectoryService`, `RationCatalogService`, `SearchService`, …);
  one access rule (`BeneficiaryAccess`) instead of four copies; the synthetic-data list reuses the database
  viewer's query. 16 new C# tests (130 total).
- Root MySQL tests (`tests/mysql`) use `TEST_DATABASE_URL` / the backend's `DATABASE_URL`, not their own
  `DB_*` settings; `run-tests.ps1 -MySql` runs them.
- C# packages patched (EF Core / JwtBearer 8.0.31, Pomelo 8.0.3, test-project pins): no known vulnerabilities.

### Fixed
- **Gateway throughput** (found by the load test): `sniffio` was missing, so every request proxied to C#
  searched the Python path on disk; and one large httpx pool slowed down as it grew. Now `sniffio` is pinned
  and the proxy uses 8 small pools in turn: at 100 users 133 → 371 req/s, p95 1.97 s → 0.46 s.
- Updating your profile with a space-padded mobile number that another account uses returned 500; now 409.
- Search: a role other than the four known ones would have seen unscoped results; it now sees nothing.

## 2026-09-25 (late night) — Thin controllers, chatbot modules, collections, contracts, E2E, `sr.ps1`

Most of this was committed in `583792e` (together with new READMEs); the rest in the following commit.

### Added
- `BeneficiaryProfileService` and `AdminDatabaseBrowserService`: the logic of `BeneficiariesController`
  (including the "citizens see only their own beneficiary" rule) and `AdminDatabaseController` moved out of
  the controllers; 10 new C# tests (104 total).
- Chatbot split into `text.py`, `intents.py`, `retrieval.py`, `responses.py` + `engine.py` (orchestration);
  identical replies to the old engine on 8 565 comparisons; evaluation 67/67.
- Synthetic `collect()` / `--collections SHARE`: past collections with stock and ledger updates, never
  below zero. 100 000-citizen run on MySQL (83 s). MySQL suite: collections for 1 000 citizens (146 tests).
- `api/openapi/`: generated Python (drift-tested) and C# API contracts (`scripts/export_openapi.py`).
- `sr.ps1`: one command for setup, run, stop, health, test, e2e, build, lint, db, synthetic, contracts, docker.
- Playwright end-to-end smoke tests (9: desktop + phone) using the installed Microsoft Edge; `run-tests.ps1 -E2E`.
- VS Code tasks named as in the brief (Build All, Synthetic Data, Python/.NET/Frontend/E2E/All Tests, …).

### Changed
- Health check labels: `[PASS]` / `[FAIL]` / `[WARNING]` / `[NOT CONFIGURED]`; `-Deep` builds C# and the frontend.
- Python seeder creates time slots from 5 days ago to 2 days ahead (like the C# seeder), so fresh
  databases have history to attach collections to.
- Public Help: "1 topic" (was "1 topics"), found by the E2E suite.
- Documentation corrected where it described features that don't exist (offline QR, eligibility calculator,
  SMS alerts, mobile app features, test libraries, forecast horizon, test counts).

### Removed
- Empty placeholder folders (`api/`, `shared/`, `atp/`, five in `frontend/src/`) and the unused root `.venv`.

## 2026-09-25 (night) — Solution file, setup, lint, schema snapshot, bookings, port clashes

### Added
- `SmartRation.sln` at the root (`dotnet restore/build/test` from the repository root).
- `scripts/development/setup.ps1` and `setup.sh`: tools check, virtualenvs, pip/npm, restore; `.env` templates only when missing.
- Frontend ESLint (`npm run lint`, flat config).
- `database/schema/smartration_schema.sql` generated from Alembic (`export_schema_sql.py`) with a drift test.
- Synthetic generator `--bookings`: one upcoming token per citizen, capacity respected; tests up to 10 000 records.
- CI: MySQL suite on `smartration_test`, AI service job, ESLint, solution build.

### Changed
- `health-check.ps1`: tools, project setup, services, port clashes and database with `[OK]/[WARNING]/[ERROR]`.
- `start-all.ps1`: waits for each service; prints `SERVICE FAILED / REASON / COMMAND`; detects ports held by other programs.
- `run-tests.ps1`: + ESLint, frontend build, database health; C# via the solution.
- Python API and AI service URLs use `127.0.0.1` (another program on `[::]:8000` was answering `localhost`).
- VS Code: `Smart Ration: …` configurations and tasks, Setup and Lint tasks, pytest discovery, format only modified lines.
- Removed empty placeholder folders (`tests/backend|e2e|frontend`, `scripts/setup|deployment`, `database/migrations|seed|diagrams`).

## 2026-09-25 (evening) — Synthetic data generator, scale tests, branding

### Added
- Central seeded synthetic-data generator `backend/SmartRation.Python/app/synthetic` and
  `scripts/generate_test_data.py --users N --seed S [--json F] [--insert]` (test databases only).
- MySQL suite `test_08_scale.py`: 1000-citizen CRUD with integrity checks; concurrency at 10/25/50/100
  (reads, creates, lost updates, bookings, stock). `/health/db`. `DATABASE_TESTING_COMPLETION_REPORT.md`.
- Favicon and Apple touch icon (emblem cropped from the supplied Ration Mitra logo).

### Changed
- Logo 1: the Ration Mitra emblem replaces the HSD2C logo in every header; HSD2C moves to the footer.
- Logo 2: the chatbot avatar and launcher use the same emblem (the drawn SVGs were removed); the assistant is
  named "Ration Mitra AI Assistant" in en/hi/mr.
- Demo mobiles `9876543210–12` → `9000000001`, `9000000051`, `9000000052` (seeders, tests, dev database rows).
- Frontend falls back to `http://localhost:8000/api` only in development; production builds use `/api`.
- C# test `ScenarioBuilder`: sequential synthetic mobiles instead of `Random`.

## 2026-09-25 (later) — Workspace, data separation, documentation

### Added
- `DATA_MODE` (synthetic | real) in both backends; real mode refused with "BLOCKED — REQUIRES EXTERNAL
  INTEGRATION"; `app/data_providers`; `data/synthetic/reference/*.json`; `data/real/README.md`. (`5ea59be`, `e159ac6`)
- `ai/` folder: chatbot knowledge, evaluation set (67 cases) + `python -m app.chatbot.evaluate`, LLM prompt template.
- Chatbot: signed-in citizens can ask about their own booking; offline state. `/health` reports AI service,
  chatbot, data mode; developer `/status` page.
- VS Code workspace (`SmartRation-HSD2C.code-workspace`), tasks, launch configurations;
  `scripts/development` (start-all, stop-all, health-check, seed-demo-data, run-tests). (`e0fe79d`, `0eba854`)
- READMEs in every main folder; docs reorganised into `docs/<area>/`; architecture set; LOCAL_SETUP; root `.env.example`.

### Changed
- Backend direction: **frozen hybrid** — C# keeps business logic; the Python migration is paused.
- Docker builds from the repository root (allow-list `.dockerignore`).

### Fixed
- `Demo:UseSynthetic*` flags were ignored; `start-dev.bat` didn't start the Python API; broken paths in
  `scripts/start-*.ps1`; `run-tests -MySql` skipped the suite; C# tests failed while the API ran.

## 2026-09-25 — Public Help, AI Assistant, fixes (`feature/python-backend-migration`)

### Added
- **Public landing page** (`/`) and **Public Help** (`/help`) — no login needed; en/hi/mr. (`8663bd9`)
- **Smart Ration AI Assistant**: floating Public Help chatbot, bottom-right. Retrieval over 25 reviewed
  articles in three languages, live public shop/scheme data, privacy and health safety rules, rate
  limits, no message text in logs. API `/api/chatbot/*`, `/api/public-help/*`. (`01d6324`, `8663bd9`)
- Chatbot branding derived from the Ration Mitra mark (`frontend/src/assets/chatbot/`).
- Frontend test runner (Vitest + Testing Library), 33 tests; frontend tests in CI.
- Root `tests/mysql` suite on `smartration_test` (connection, schema, CRUD, transactions). (`4491b6c`)
- Docs: `PROJECT_AUDIT.md` (new), `PROJECT_STATUS.md`, `docs/chatbot/CHATBOT_ARCHITECTURE.md`, `docs/testing/TESTING.md`,
  `CONTRIBUTING.md`, `SECURITY.md`, this changelog; nginx example.

### Changed
- Frontend now calls the Python backend (`:8000`); unmigrated routes are proxied to C#.
- Test helpers moved out of `conftest` into `py_testkit` / `ai_testkit` / `mysql_suite.support`;
  pytest runs from each backend and from the repository root.

### Fixed
- **Registration deadlock under concurrency** (35 of 100 simultaneous sign-ups failed with MySQL 1213)
  in both backends — placeholder codes on UNIQUE columns. (`4491b6c`, `53f6080`)
- 500 responses had no `X-Request-ID` and their log entries no request id. (`4491b6c`)
- C# per-IP rate limits treated every proxied request as 127.0.0.1 (forwarded headers). (`53f6080`)
- pytest collection broken after `tests/__init__.py` removal; root `import_mode` setting was ignored.
- Chatbot reply formatting with several blank lines; shop search matched every shop's name.

## 2026-09-24 — Python backend foundation and operations
- Python FastAPI backend with fallback proxy to C#; `/api/auth` migrated (Argon2id, cross-backend
  tokens). (`37b2c24`, `4663fd1`)
- Alembic owns the schema (`0001_initial`, live DB stamped with zero drift); setup/verify/seed/reset
  scripts; MySQL backup/restore scripts. (`5950969`)
- `/ready`, typed models, ruff + mypy. (`1380d01`)
- Docker, docker-compose, GitHub Actions CI, documentation set. (`e82570e`)
- MySQL test suite (122 tests, 100 records) and step-by-step guide. (`5f926dc`)
- JWT key and QR secret moved out of tracked config (QR secret preserved). (`4c983e2`)

## 2026-09-19 → 2026-09-22 — Initial platform
- React dashboard for rural users, shops and officials; ASP.NET Core API; frontend wired to the API;
  QR-based beneficiary verification, entitlements and Smart Ration Map. (`c56a207` … `29fa9d0`)
