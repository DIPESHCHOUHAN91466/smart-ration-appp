# tests — cross-component tests

**What:** tests that span components — the whole stack in a browser, a deployment from the outside, the
shared MySQL database, and the contracts between C#, Python and JavaScript. **Why:** each app's own tests
can only see that app; these catch what breaks between them.

| Folder | What it tests | Needs | Run (repository root) |
|---|---|---|---|
| `e2e/` | browser journeys through frontend → gateway → C# API → MySQL (Playwright, installed Edge, desktop + phone; never signs in) | the stack running (`.\sr.ps1 run`) | `.\sr.ps1 e2e` (first time: `npm install` in `tests\e2e`) |
| `smoke/` | a deployment from the outside: health, readiness, database, chatbot, auth enforcement, security headers, the website | a URL | `.\sr.ps1 smoke <url>` or `pytest tests/smoke --base-url <url>` (skipped without one) |
| `integration/mysql/` | the shared MySQL server directly: connection, `utf8mb4`, schema (InnoDB, keys, indexes), CRUD, transactions, SQL-injection payloads | `smartration_test` | `backend\SmartRation\.venv\Scripts\python -m pytest tests/integration/mysql` |
| `regression/` | values C#, Python and JS must agree on (enums, QR contract, roles, ration types) + the register of every fixed bug and its test | nothing | `backend\SmartRation\.venv\Scripts\python -m pytest tests/regression` |

`pytest` from the repository root (with `backend\SmartRation\.venv`) runs the gateway, AI service, MySQL
and regression suites together (`pytest.ini`); `.\scripts\testing\run-tests.ps1 -MySql -E2E` runs everything.

**Where the other tests live** (next to the code they test):

| Suite | Location | Count (2026-09-28) |
|---|---|---|
| Python gateway: unit, api, integration, security, performance | `backend/SmartRation/tests/` | 296 (+145 MySQL-only, skipped without `TEST_DATABASE_URL`) |
| MySQL suite (CRUD, injection, 1,000 records, concurrency 10–100, integrity) | `backend/SmartRation/tests/integration/mysql_suite/` | 146 |
| Contract tools (C# vs Python, live, manual) | `backend/SmartRation/tests/contract/` | — |
| Chatbot evaluation | `ai/chatbot/evaluation/` (`python -m app.ai.chatbot.evaluate`) | 67 cases |
| AI service | `ai/tests/` | 58 |
| C# API | `backend/SmartRation.Api.Tests/` | 136 |
| Frontend unit + component | `frontend/tests/unit/` | 51 |

**Does NOT belong here:** tests of a single app (keep them next to that app); anything that touches the
real `smartration` database — every MySQL test refuses a database whose name doesn't end in `_test`.

Strategy: [../docs/testing/TESTING.md](../docs/testing/TESTING.md).
