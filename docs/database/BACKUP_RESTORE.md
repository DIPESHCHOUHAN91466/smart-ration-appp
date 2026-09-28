# Backup and restore

Scripts: `scripts/database/backup.ps1`, `scripts/database/restore.ps1` (Windows PowerShell 5.1+,
MySQL 8 client tools in `C:\Program Files\MySQL\MySQL Server 8.0\bin`, overridable with `-MySqlBin`).
Credentials come from environment variables and go into a temporary MySQL option file that is
deleted afterwards, so they never appear on the command line.

## Back up

```powershell
$env:SMARTRATION_DB_USER = "smartration_app"
$env:SMARTRATION_DB_PASSWORD = "<password>"      # from your .env; don't paste it into files
.\scripts\database\backup.ps1
```

- `mysqldump --single-transaction` (consistent snapshot without locking), with routines,
  triggers and events, `--hex-blob`, utf8mb4.
- Output: `database/backups/smartration_<yyyyMMdd_HHmmss>.sql.gz` plus a `.sha256` file.
  The script checks for mysqldump's completion marker before compressing, and never overwrites.
- The folder is git-ignored. **Copy backups off the machine**; a backup on the same disk doesn't
  survive disk loss.

Always back up before: applying a migration, restoring, running `reset_database.py` (it does so
itself), or any manual SQL.

## Restore (replaces the database contents)

```powershell
# stop the C# and Python APIs first
.\scripts\database\restore.ps1 -BackupFile .\database\backups\smartration_20260924_134123.sql.gz -Confirm RESTORE_SMARTRATION
cd backend\SmartRation; .venv\Scripts\python scripts\verify_database.py
```

The restore script: refuses without `-Confirm RESTORE_SMARTRATION` → verifies the SHA-256 checksum →
takes a **safety backup of the current state** (skip only with `-SkipSafetyBackup`) → checks the dump
is complete → loads it.

After restoring an older backup, run `scripts/setup_database.py`: if the backup predates a migration,
it applies the missing revisions (or adopts a pre-Alembic dump with `stamp`).

## Status

- Backup: tested against the live database (26 tables, completion marker present, no password in
  the dump). Backups exist from 2026-09-24 13:34 and 13:41 (before the Alembic stamp).
- Restore: **not yet tested end to end.** The app account can't create a scratch database, so a
  restore rehearsal needs a root-created scratch schema (`smartration_restore_test`), with the
  restore run against it via `-Database smartration_restore_test`, then `verify_database.py`
  pointed at it. Do this before relying on restore.
