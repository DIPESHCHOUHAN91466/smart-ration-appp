# Testing

## What exists

| Suite | Where | Runs against | Count | Command |
|---|---|---|---|---|
| Python backend unit/API | `backend/SmartRation.Python/tests/` | SQLite temp files | 136 | `.venv\Scripts\python -m pytest` (in that folder) |
| MySQL suite (100 records) | `backend/SmartRation.Python/tests/mysql_suite/` | `smartration_test` | 122 | set `TEST_DATABASE_URL`, then `… -m pytest tests/mysql_suite` |
| Root MySQL tests | `tests/mysql/` | `smartration_test` (root `.env`) | 24 | from the repo root: `backend\SmartRation.Python\.venv\Scripts\python -m pytest tests/mysql` |
| AI service | `backend/SmartRation.AI/tests/` | SQLite | 46 | `.venv\Scripts\python -m pytest` (in that folder) |
| C# API | `backend/SmartRation.Api.Tests/` | in-memory | 86 | `dotnet test backend/SmartRation.Api.Tests` |
| Frontend | `frontend/tests/unit/` | jsdom | 33 | `npm test` (in `frontend`) |
| Contract (live) | `backend/SmartRation.Python/tests/contract/` | both running APIs | 36 + 23 | `compare_proxy.py`, `auth_interop.py` |
| Database verify | `backend/SmartRation.Python/scripts/verify_database.py` | the configured DB | — | read-only check |

Everything Python can also be collected from the repository root with the Python backend's virtualenv
(`pytest.ini` at the root lists all three test folders; `--import-mode=importlib`).

## Coverage by area

| Area | Tests |
|---|---|
| Authentication, refresh rotation, Argon2 upgrade, cross-backend tokens | `test_auth.py`, `auth_interop.py`, C# `PasswordHashesTests` |
| Authorization (roles) | `test_auth.py`, C# service tests |
| SQL injection | MySQL suite `test_03_security.py` (16 payloads × API/ORM/raw driver), `tests/mysql/test_crud.py` |
| Rate limiting | `test_auth.py`, `test_public_help_api.py` |
| Schema, migrations, drift | `test_schema_compat.py`, `test_db_scripts.py`, `verify_database.py`, MySQL suite `test_01` |
| CRUD, transactions, integrity, concurrency | MySQL suite `test_02`, `test_05`, `test_07`; `tests/mysql/*` |
| Error handling, logging without secrets | MySQL suite `test_06`, `test_health_and_errors.py` |
| Proxy parity with C# | `test_proxy.py`, `compare_proxy.py` |
| Chatbot + Public Help | `test_chatbot_engine.py`, `test_public_help_api.py`, frontend `chatbot.test.jsx`, `publicPages.test.jsx` |
| Translations complete (en/hi/mr) | frontend `i18n.test.js`, backend knowledge-integrity tests |
| QR, OTP, collection, inventory, entitlement | C# tests (86) — still served by C# |

## Gaps (honest list)

- **No end-to-end browser automation** (Playwright/Cypress). Browser checks were done manually for
  this release (see PROJECT_STATUS.md).
- Frontend tests cover the new public pages and chatbot only; existing dashboards have none.
- No load tests beyond the MySQL suite's 100-record and 40-thread checks.
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
