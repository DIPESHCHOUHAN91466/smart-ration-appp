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
3. Database credentials specified in the project root `.env` or environment variables:
   ```env
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=smartration_app
   DB_PASSWORD=your_password_here
   DB_NAME=smartration_test
   ```

> **Safety Guard:** Every test in this suite validates that the database name ends with `_test`. Tests will immediately refuse to execute against any production or default database name.

## Running the Suite

From the repository root:
```powershell
backend\SmartRation.Python\.venv\Scripts\python -m pytest tests/mysql -v
```

Or using the project test orchestrator:
```powershell
.\scripts\development\run-tests.ps1 -MySql
```
