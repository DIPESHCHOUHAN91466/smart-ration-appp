# tests/mysql — Direct MySQL Integration Test Suite

Direct database integration tests verifying MySQL server configuration, table schema definitions, CRUD operations, transaction isolation, and SQL injection resilience against the test database (`smartration_test`).

## Overview

Unlike unit tests that mock database contexts, this test suite connects directly to a live MySQL 8 instance using `pymysql` and SQLAlchemy.

| File | Focus Area |
|---|---|
| `test_database.py` | Connection handshake, character set verification (`utf8mb4`), timezone, password masking in error outputs, connection timeout behavior |
| `test_schema.py` | Verification that all tables use the `InnoDB` engine with `utf8mb4_0900_ai_ci` collation, presence of primary keys, indexes, and foreign keys |
| `test_crud.py` | 100-record batch inserts, update/read latency, SQL injection resilience across multiple payload vectors (`' OR '1'='1`, `UNION SELECT`, `; DROP TABLE`), null handling, max multibyte string storage |
| `test_transactions.py` | Explicit transaction commit/rollback, read uncommitted isolation checks, context-manager automatic rollbacks on exception, foreign-key constraint enforcement |

## Prerequisites

1. MySQL 8 running locally on port 3306.
2. The `smartration_test` database created.
3. Nothing extra to configure: the connection comes from the project's one database setting
   (`tests/mysql/config.py`), in this order:
   1. `TEST_DATABASE_URL` (what `run-tests.ps1 -MySql` and CI set),
   2. otherwise `DATABASE_URL` in `backend/SmartRation/.env`, pointed at `smartration_test`,
   3. otherwise the legacy `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` in the root `.env`.

   Run: `.\scripts\testing\run-tests.ps1 -MySql`, or from the repository root
   `backend\SmartRation\.venv\Scripts\python -m pytest tests/mysql`.

> **Safety Guard:** Every test in this suite validates that the database name ends with `_test`. Tests will immediately refuse to execute against any production or default database name.

## Running the Suite

From the repository root:
```powershell
backend\SmartRation\.venv\Scripts\python -m pytest tests/mysql -v
```

Or using the project test orchestrator:
```powershell
.\scripts\testing\run-tests.ps1 -MySql
```
