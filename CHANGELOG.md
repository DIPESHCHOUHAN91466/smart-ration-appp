# Changelog

All notable changes. Dates are commit dates; hashes refer to this repository.

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
