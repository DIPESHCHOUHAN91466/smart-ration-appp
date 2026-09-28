# database — MySQL outside the application code

**What:** everything about the MySQL database that a DBA, reviewer or operator needs without reading
Python: the one-time setup script, the schema and each migration as SQL, the seed data, and read-only
integrity checks.

**Why:** the database outlives any single backend. Creating it, reviewing schema changes, seeding a demo
installation and checking the data are tasks with their own safety rules.

| Folder | Contents | Written by |
|---|---|---|
| `schema/mysql-setup.sql` | creates the `smartration` database, the `smartration_app` account and the **read-only** `smartration_ai` account. Copy it to `database/mysql-setup.local.sql` (git-ignored) before filling in passwords | hand |
| `schema/smartration_schema.sql` | the whole schema at the current Alembic head (26 tables incl. `alembic_version`) | generated |
| `migrations/<revision>.upgrade.sql` | what each Alembic revision changes, for DBAs who must apply SQL by hand (also sets `alembic_version`). Later revisions also get a `.downgrade.sql`; the initial one does not — undoing it drops everything, so restore a backup instead | generated |
| `seeds/` | synthetic reference data (`seeds/synthetic/*.json`, all marked `isSynthetic`) and [what real data would require](seeds/REAL_DATA.md) | hand |
| `queries/` | read-only integrity checks, one rule per file (over-booked slots, negative stock, collections without items or with open tokens, unmasked Aadhaar, duplicate e-mails, counter drift, shop owners without a shop) | hand |
| `backups/` | output of `scripts/database/backup.ps1` — **git-ignored, may contain personal data** | script |

**Does NOT belong here:** the schema's source of truth — that is the Alembic migrations in
`backend/SmartRation/migrations` (Python code, applied with `alembic upgrade head` / `setup_database.py`);
passwords; real personal data.

## Run

```powershell
mysql -u root -p < database\mysql-setup.local.sql            # one time, as root
.\scripts\database\seed-demo-data.ps1                          # schema (Alembic) + synthetic reference data
cd backend\SmartRation
.venv\Scripts\python scripts\verify_database.py                # schema matches the models (read-only)
.venv\Scripts\python scripts\check_data_integrity.py           # database/queries (read-only; exit 1 on errors)
.venv\Scripts\python scripts\export_schema_sql.py              # regenerate schema/ and migrations/ after a new revision
```

`export_schema_sql.py --check` runs in the tests, so a migration committed without refreshed SQL fails.
`check_data_integrity.py` prints ids and counts only — never names, e-mails or Aadhaar values — and runs every
query inside a transaction that is rolled back. CI runs it with `--strict` after seeding MySQL 8.

## Adding an integrity check

Create `queries/NN_<name>.sql` with one `SELECT` whose first column is `id`, and this header:

```sql
-- check: <name>
-- severity: error | warning
-- why: the rule, and where the application enforces it
```

Then add a case to `backend/SmartRation/tests/integration/test_data_integrity.py` that breaks the rule and
expects the check to report it.

**Connects:** Python API and C# API (read/write, `smartration_app`), AI service (read-only, `smartration_ai`).
Test suites use a separate `smartration_test` database.

> History: the schema was created by EF Core migrations in the C# API until 2026-09-24; Alembic owns it
> since then (the existing database was adopted with zero drift). The C# API still runs its already
> complete EF history on startup, which changes nothing. Do not add EF migrations.

Architecture: [../docs/database/DATABASE_ARCHITECTURE.md](../docs/database/DATABASE_ARCHITECTURE.md) ·
Backups: [../docs/database/BACKUP_RESTORE.md](../docs/database/BACKUP_RESTORE.md) ·
Test plan: [../docs/database/DB_TESTING.md](../docs/database/DB_TESTING.md).
