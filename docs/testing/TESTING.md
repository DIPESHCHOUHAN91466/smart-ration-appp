# Testing

## What exists (counts verified 2026-09-28)

| Layer | Suite | Where | Runs against | Count | Command |
|---|---|---|---|---|---|
| unit | Python gateway | `backend/SmartRation/tests/unit/` | nothing | chatbot engine, masking, passwords/tokens, env templates | `.venv\Scripts\python -m pytest tests\unit` (in `backend/SmartRation`) |
| api | Python gateway | `backend/SmartRation/tests/api/` | SQLite temp files | auth, health, errors, proxy, Public Help, `/api/v1`, website, contract | `… -m pytest tests\api` |
| integration | Python gateway | `backend/SmartRation/tests/integration/` | SQLite (+ MySQL for schema compatibility) | repositories, cleanup worker, integrity checks, DB scripts, synthetic generator, schema snapshot, backup script | `… -m pytest tests\integration` |
| security | Python gateway | `backend/SmartRation/tests/security/` | SQLite | forged / expired / `alg=none` tokens, roles, SQL injection, error hygiene, CORS, log hygiene | `… -m pytest tests\security` |
| performance | Python gateway | `backend/SmartRation/tests/performance/` | in-process | latency budgets (chatbot 2 ms, liveness 6 ms, lookup 0.5 ms p95 measured; budgets 4–25× that) | `… -m pytest tests\performance` |
| | **gateway total** | | | **296** (+145 MySQL-only, skipped without `TEST_DATABASE_URL`) | `.venv\Scripts\python -m pytest` |
| integration | MySQL suite (100 adversarial + 1000 generated records; concurrency 10/25/50/100) | `backend/SmartRation/tests/integration/mysql_suite/` | `smartration_test` | 146 | set `TEST_DATABASE_URL`, then `… -m pytest tests/integration/mysql_suite` |
| integration | Root MySQL tests | `tests/integration/mysql/` | `smartration_test` | 24 | from the repo root: `backend\SmartRation\.venv\Scripts\python -m pytest tests/integration/mysql` |
| regression | Cross-component contracts + bug register | `tests/regression/` | source files | 21 | `… -m pytest tests/regression` (repo root) |
| unit/api | AI service | `ai/tests/` | SQLite | 58 | `.venv\Scripts\python -m pytest` (in `ai/`) |
| unit/integration | C# API | `backend/SmartRation.Api.Tests/` | SQLite in-memory | 136 | `dotnet test SmartRation.sln -c Release` (repo root) |
| unit | Frontend | `frontend/tests/unit/` | jsdom | 51 | `npm test` (in `frontend`) |
| e2e | Browser journeys (desktop + phone) | `tests/e2e/` | the running stack | 9 | `.\sr.ps1 e2e` |
| smoke | Post-deployment | `tests/smoke/` | any URL | 10 | `.\sr.ps1 smoke <url>` |
| evaluation | Chatbot (en/hi/mr) | `ai/chatbot/evaluation/` | knowledge base | 67 cases | `python -m app.ai.chatbot.evaluate` |
| evaluation | Forecast accuracy | `ai/evaluation/report.py` | read-only DB | per shop × item | `ai\.venv\Scripts\python -m ai.evaluation.report` |
| data | Integrity checks | `database/queries/` | the configured DB | 8 rules | `.\sr.ps1 db integrity` |
| load | HTTP load (10/100/1000 concurrent citizens + rate-limit burst) | `backend/SmartRation/scripts/load_test.py` | the running stack | — | `.\sr.ps1 load` — results: [LOAD_TESTING.md](LOAD_TESTING.md) |
| contract (manual) | C# vs Python, live | `backend/SmartRation/tests/contract/` | both running APIs | 36 + 23 checks | `compare_proxy.py`, `auth_interop.py` |

The root `pytest.ini` collects the gateway, AI, root MySQL and regression suites in one run (399 passed
without `TEST_DATABASE_URL`). `.\scripts\testing\run-tests.ps1 -MySql -E2E` runs everything.

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
| QR, OTP, collection, inventory, entitlement, seeder invariants | C# tests (136) — still served by C# |
| Security controls (tokens, roles, injection, error/log hygiene, CORS) | `tests/security/test_security_controls.py` |
| Cross-language contracts (enums, QR, roles, ration types) | `tests/regression/test_cross_component_contracts.py` |
| Data integrity rules | `tests/integration/test_data_integrity.py` + `database/queries/` |
| AI stages (series, models, backtests, selection, report) | `ai/tests/test_stages.py` |

## Gaps (honest list)

- End-to-end browser tests (Playwright, 9) run locally against the running stack, not in CI.
- Frontend tests cover the public pages, chatbot, profile, status page and shared formatting; most dashboard pages have none.
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
