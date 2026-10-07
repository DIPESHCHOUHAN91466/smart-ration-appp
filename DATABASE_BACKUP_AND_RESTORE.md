# Database backup and restore

How Smart Ration's MySQL data is backed up, restored, migrated and rolled back, and the evidence that a restore
really works. Detailed script options: [docs/database/BACKUP_RESTORE.md](docs/database/BACKUP_RESTORE.md).

## Restore tested (2026-10-07)

A backup only counts once a restore has worked. Drill on the local database:

```
backup: smartration_20261007_082712.sql.gz 1542 KB, sha256 file present
tables: 29 live, 29 restored; identical (rows + CHECKSUM TABLE): 29; total rows 191783
```

The first run of the drill found a real defect: **the Windows restore script turned every Hindi/Marathi character
(and symbols like "—") into "?"**: complaint text came back as `???? ?????? ???` while the script reported
success. Windows PowerShell 5.1 re-encodes text as ASCII when piping it into a program. Fixed: `restore.ps1` now
lets `mysql` read the file itself (`--execute="source <file>"`). Backups were never affected (mysqldump writes the
file directly; the Hindi text is intact in every `.sql.gz`).

Repeat the drill at any time (Windows, nothing else writing to the database):

```powershell
backend\SmartRation\.venv\Scripts\python scripts\database\restore-drill.py            # new backup, then drill
backend\SmartRation\.venv\Scripts\python scripts\database\restore-drill.py <file.sql.gz>   # an existing backup
```

It restores into `smartration_test` (the throwaway database the integration tests rebuild), compares every table
with the live one, and empties `smartration_test` again. The live database is only read.

## Back up

| Where | How | Schedule / retention |
|---|---|---|
| Local / Windows server | `scripts\database\backup.ps1` (credentials from `SMARTRATION_DB_USER` / `SMARTRATION_DB_PASSWORD`) | Before every migration, restore or manual SQL; copy files off the machine |
| Linux server, cron or CI | `deployment/scripts/backup-mysql.sh` (`DB_*` variables, optional `MYSQL_SSL_CA`) | `KEEP_DAYS` (default 14) |
| Aiven (cloud) | The provider's automatic backups, plus `backup-mysql.sh` from a scheduled job for a copy outside Aiven | Daily; check the retention of the chosen plan in the Aiven console |

All dumps: `mysqldump --single-transaction` (consistent, no locks), routines, triggers, events, utf8mb4, a
`.sha256` file, and a check for mysqldump's completion marker. Backups contain citizens' personal data: keep them
encrypted at rest and access-controlled.

## Restore (replaces the target database's contents)

1. Stop the API (or put the site in maintenance).
2. `.\scripts\database\restore.ps1 -BackupFile <file.sql.gz> -Confirm RESTORE_SMARTRATION`: verifies the checksum
   and completeness, takes a **safety backup of the current state first**, then restores.
   Linux: `gunzip -c <file.sql.gz> | mysql --default-character-set=utf8mb4 <db>` (byte-for-byte, no re-encoding).
3. `python backend/SmartRation/scripts/verify_database.py`, start the API, check `/health/db` and sign in.

Cloud: restore an Aiven backup **into a new service** first (provider console), point a staging copy of the API at
it, check it, and only then switch production `DATABASE_URL`. Never restore over production without a fresh backup.

## Migrations

1. Back up (above) and keep the file name.
2. Review the Alembic migration (`backend/SmartRation/migrations/versions/`).
3. Apply: `alembic upgrade head` with `MIGRATION_DATABASE_URL` (the schema-changing account; the running API uses a
   rows-only account, see `database/schema/mysql-least-privilege.sql`). On Render the container applies migrations on
   start (`RUN_DB_SETUP=true`).
4. Verify: run the API tests against a copy, `/health/db`, a sign-in and one booking.

## Roll back

- **Code only** (no schema change): redeploy the previous image/commit (see [ROLLBACK_PROCEDURE.md](ROLLBACK_PROCEDURE.md)).
- **Schema change**: `alembic downgrade -1` when the migration has a tested downgrade; otherwise restore the backup
  taken in step 1 of the migration. Data written after that backup is lost, so restoring is the last resort.
