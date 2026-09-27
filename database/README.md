# database — MySQL setup and operations

**What is this?** Everything about the MySQL database that isn't application code: the one-time setup
script, backup and restore scripts, and reference folders.

**Why does it exist?** The database outlives any single backend; creating it, backing it up and
restoring it are operational tasks with their own safety rules.

**What belongs here:** `mysql-setup.sql` (creates the `smartration` database, the `smartration_app`
account and the **read-only** `smartration_ai` account — copy to `*.local.sql`, which is git-ignored,
before filling in passwords), `mysql/backup.ps1`, `mysql/restore.ps1` (see [mysql/README.md](mysql/README.md)).
**What does NOT:** the schema definition and migrations — those are code, owned by **Alembic** in
`backend/SmartRation/app/db/migrations` (revision `0001_initial` = the 25 tables); setup/verify/
seed/reset scripts live in `backend/SmartRation/scripts`; synthetic reference data lives in
`data/synthetic`. Never commit passwords or backups.

> History: the schema used to be created by EF Core migrations in the C# API (MySQL and SQLite). Since
> 2026-09-24 Alembic owns it; the existing database was adopted with zero drift. Do not add EF migrations.
> The C# API still runs its (already complete) EF migration history on startup, which changes nothing.

**How do I run it?**
```
mysql -u root -p < database\mysql-setup.local.sql            # one time, as root
.\scripts\development\seed-demo-data.ps1                     # schema + synthetic reference data
backend\SmartRation\.venv\Scripts\python backend\SmartRation\scripts\verify_database.py
```

**How does it connect?** Python API (read/write, `smartration_app`), C# API (read/write, same account),
AI service (read-only, `smartration_ai`). Test suites use a separate `smartration_test` database.

Architecture: [../docs/database/DATABASE_ARCHITECTURE.md](../docs/database/DATABASE_ARCHITECTURE.md) ·
Backups: [../docs/database/BACKUP_RESTORE.md](../docs/database/BACKUP_RESTORE.md) ·
Test plan: [../docs/database/DB_TESTING.md](../docs/database/DB_TESTING.md).

`schema/smartration_schema.sql` is a **generated, read-only** SQL view of the Alembic migrations (every
table, column, key and index) for people who want to read the schema as SQL. Regenerate it after a
migration with `backend\SmartRation\scripts\export_schema_sql.py`; a test fails if it is out of
date. Never apply it to a database — `setup_database.py` / `alembic upgrade head` do that.
(The empty `migrations/`, `seed/` and `diagrams/` placeholders from the original scaffold were removed:
migrations live in Alembic, seeds in `data/synthetic` + `seed_database.py`.)
