# backend/SmartRation/tests — Python gateway tests

One folder per test layer. `pytest` from `backend/SmartRation` runs all of them; tests that need MySQL skip
themselves when no database is configured (they never touch the real `smartration` data — the MySQL
suite uses `smartration_test` through `TEST_DATABASE_URL`).

| Folder | What it tests | Needs |
|---|---|---|
| `unit/` | Pure functions: chatbot engine (retrieval in en/hi/mr, safety rules, knowledge integrity), masking, password hashing, JWT and refresh tokens, time formats | nothing |
| `api/` | HTTP behaviour through the FastAPI app: auth (register, login, refresh, logout, C# compatibility), health and readiness, error envelopes, `/api/v1` alias, proxy to the C# API, Public Help and chatbot routes, data mode, serving the built frontend, the OpenAPI contract | SQLite temp files |
| `integration/` | Code + a real database: repositories, the cleanup worker, database scripts (setup / seed / verify / reset), synthetic data generator, schema snapshot, models vs live MySQL (`test_schema_compat.py`) | SQLite; MySQL for schema compatibility |
| `integration/mysql_suite/` | MySQL 8 suite: CRUD, SQL-injection attempts, 1,000 records, concurrency 10–100, error handling, data integrity, scale | `TEST_DATABASE_URL` → `smartration_test` |
| `security/` | Attacks: missing / expired / forged / `alg=none` tokens, wrong issuer or audience, role violations, SQL injection at login, internal details in 500s, CORS from unknown origins, forged request ids, secrets in logs | SQLite |
| `performance/` | Latency budgets for hot paths (chatbot reply, liveness, indexed user lookup), in-process. Capacity under 10 / 100 / 1,000 users is measured with `scripts/load_test.py` against a running stack | SQLite |
| `contract/` | Manual tools (not collected by pytest): compare gateway and C# responses, cross-check tokens | both servers running |

Shared helpers: `conftest.py` (the `make_client` fixture) and `py_testkit.py` (`make_settings`, `BACKEND_ROOT`,
`REPO_ROOT`). `pytest.ini` puts `tests` and `tests/integration` on the import path, so helpers are imported by
unique module names (`py_testkit`, `mysql_suite.*`) and no folder needs an `__init__.py`.

## Running

From `backend/SmartRation`:

```powershell
.venv\Scripts\python -m pytest                       # everything (MySQL-only tests skip without a database)
.venv\Scripts\python -m pytest tests\unit             # one layer
.venv\Scripts\python -m pytest tests\security -v
```

MySQL suite on the separate test database (the script builds the URL from `.env` without printing it):

```powershell
$env:TEST_DATABASE_URL = .venv\Scripts\python scripts\test_database_url.py
.venv\Scripts\python -m pytest tests\integration\mysql_suite
Remove-Item Env:TEST_DATABASE_URL
```

Or from the repository root: `.\scripts\testing\run-tests.ps1 -MySql`.

Contract comparison (both servers running): `.venv\Scripts\python tests\contract\compare_proxy.py`.

## Adding a test

- A bug fix gets a test in the layer where the bug lived; a fix found in production also gets a note in the test's docstring.
- New endpoints: success, validation failure, 401/403 where protected, and the error envelope in `api/`.
- Never use real personal data; use the synthetic generator (`app.synthetic`) or the `@example.com` users in fixtures.
