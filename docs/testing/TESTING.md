# Testing

## What exists

| Suite | Where | Runs against | Count | Command |
|---|---|---|---|---|
| Python backend unit/API | `backend/SmartRation/tests/` | SQLite temp files | 221 | `.venv\Scripts\python -m pytest` (in that folder) |
| MySQL suite (100 adversarial + 1000 generated records; concurrency 10/25/50/100) | `backend/SmartRation/tests/integration/mysql_suite/` | `smartration_test` | 146 | set `TEST_DATABASE_URL`, then `… -m pytest tests/integration/mysql_suite` |
| Root MySQL tests | `tests/integration/mysql/` | `smartration_test` (root `.env`) | 24 | from the repo root: `backend\SmartRation\.venv\Scripts\python -m pytest tests/integration/mysql` |
| AI service | `ai/tests/` | SQLite | 58 | `.venv\Scripts\python -m pytest` (in `ai/`; lint: `ruff check ai` from the root) |
| C# API | `backend/SmartRation.Api.Tests/` | in-memory (SQLite) | 130 | `dotnet test SmartRation.sln -c Release` (repository root) |
| Frontend | `frontend/tests/unit/` | jsdom | 45 | `npm test` (in `frontend`) |
| Contract (live) | `backend/SmartRation/tests/contract/` | both running APIs | 36 + 23 | `compare_proxy.py`, `auth_interop.py` |
| HTTP load (10/100/1000 concurrent citizens + rate-limit burst) | `backend/SmartRation/scripts/load_test.py` | the running stack | — | `.\sr.ps1 load` — results: [LOAD_TESTING.md](LOAD_TESTING.md) |
| Database verify | `backend/SmartRation/scripts/verify_database.py` | the configured DB | — | read-only check |

Everything Python can also be collected from the repository root with the Python backend's virtualenv
(`pytest.ini` at the root lists all three test folders; `--import-mode=importlib`).

## Coverage by area

| Area | Tests |
|---|---|
| Authentication, refresh rotation, Argon2 upgrade, cross-backend tokens | `test_auth.py`, `auth_interop.py`, C# `PasswordHashesTests` |
| Authorization (roles) | `test_auth.py`, C# service tests |
| SQL injection | MySQL suite `test_03_security.py` (16 payloads × API/ORM/raw driver), `tests/integration/mysql/test_crud.py` |
| Rate limiting | `test_auth.py`, `test_public_help_api.py` |
| Schema, migrations, drift | `test_schema_compat.py`, `test_db_scripts.py`, `verify_database.py`, MySQL suite `test_01` |
| CRUD, transactions, integrity, concurrency | MySQL suite `test_02`, `test_05`, `test_07`, `test_08_scale` (1000 records; 10/25/50/100 concurrent reads, creates, updates, bookings, stock issues); `tests/integration/mysql/*` |
| Synthetic data generator (determinism, reserved ranges, validation, insert, CLI guards) | `test_synthetic_data.py` |
| Error handling, logging without secrets | MySQL suite `test_06`, `test_health_and_errors.py` |
| Proxy parity with C# | `test_proxy.py`, `compare_proxy.py` |
| Chatbot + Public Help | `test_chatbot_engine.py`, `test_public_help_api.py`, frontend `chatbot.test.jsx`, `publicPages.test.jsx` |
| Translations complete (en/hi/mr) | frontend `i18n.test.js`, backend knowledge-integrity tests |
| QR, OTP, collection, inventory, entitlement | C# tests (94) — still served by C# |

## Gaps (honest list)

- End-to-end browser tests (Playwright, 9) run locally against the running stack, not in CI.
- Frontend tests cover the new public pages and chatbot only; existing dashboards have none.
- HTTP load tests are read-only and run on one machine ([LOAD_TESTING.md](LOAD_TESTING.md)); write paths under
  concurrency are covered at the database level (up to 1000 records and 100 concurrent operations).
- Restore of a MySQL backup has not been rehearsed (see BACKUP_RESTORE.md).

## CI

`.github/workflows/ci.yml`: Python (3.13, 3.14) lint + mypy + schema setup/seed/verify on MySQL 8 +
pytest; C# tests; frontend `npm test` + build; Docker build + smoke test. The MySQL suite and contract
tests need a dedicated database / running servers and are run locally.

## Rules

- Tests never touch the real `smartration` database: the MySQL suites refuse any database whose name
  doesn't end in `_test`.
- Fixtures use synthetic data only (`example.test` emails, no real Aadhaar).
- A bug fix comes with the test that would have caught it (e.g. the registration deadlock → the
  100-concurrent-registrations test).
