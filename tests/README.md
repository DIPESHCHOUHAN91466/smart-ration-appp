# tests — cross-component tests

**What is this?** Tests that don't belong to one application. Today: `mysql/`, connection, schema,
CRUD and transaction tests run directly against the `smartration_test` MySQL database.

**Why does it exist?** Some checks are about the shared database itself rather than one backend.

**Where the other tests live** (each next to the code it tests):

| Suite | Location | Count |
|---|---|---|
| Python API (unit + API) | `backend/SmartRation/tests/` | 164 |
| MySQL suite (100 records: CRUD, injection, performance, concurrency, errors, integrity) | `backend/SmartRation/tests/mysql_suite/` | 122 |
| Contract tests (C# vs. Python, live) | `backend/SmartRation/tests/contract/` | 36 + 23 checks |
| Chatbot evaluation | `ai/chatbot/evaluation/` (+ `app.ai.chatbot.evaluate`) | 67 cases |
| AI service | `backend/SmartRation.AI/tests/` | 46 |
| C# API | `backend/SmartRation.Api.Tests/` | 94 |
| Frontend | `frontend/tests/unit/` | 36 |

**What belongs here:** tests that span components. **What does NOT:** tests of a single app (keep them
next to that app); anything that touches the real `smartration` database — every MySQL test refuses a
database whose name doesn't end in `_test`.

**How do I run it?** Everything: `.\scripts\development\run-tests.ps1` (add `-MySql` for database suites).
This folder only, from the repo root: `backend\SmartRation\.venv\Scripts\python -m pytest tests/mysql`
(needs `DB_*` in the root `.env`, `DB_NAME=smartration_test`).

The empty `backend/`, `frontend/`, `e2e/` folders are placeholders from the original scaffold; there are
no end-to-end (browser automation) tests yet. Strategy: [../docs/testing/TESTING.md](../docs/testing/TESTING.md).
