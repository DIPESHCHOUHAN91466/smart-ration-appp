# scripts/database — seed, back up and restore

**What:** PowerShell scripts for the `smartration` database. **Why:** every schema change, restore or
reset starts with a backup; restores must never lose the current data; a demo installation needs its
synthetic data loaded safely.
**Belongs here:** `seed-demo-data.ps1`, `backup.ps1`, `restore.ps1`. Backups are written to
`database/backups/` (git-ignored, may contain personal data).
**Doesn't:** schema or migrations (Alembic, in the Python backend), real credentials. Linux servers use
`deployment/scripts/backup-mysql.sh` (same dump options and file names).

**Run:**
```
.\scripts\database\seed-demo-data.ps1                                  # schema + synthetic data into EMPTY tables only
$env:SMARTRATION_DB_USER = "smartration_app"; $env:SMARTRATION_DB_PASSWORD = "<password>"
.\scripts\database\backup.ps1                                          # → database\backups\smartration_<timestamp>.sql.gz + .sha256
.\scripts\database\restore.ps1 -BackupFile <file> -Confirm RESTORE_SMARTRATION   # verifies checksum, backs up first
```
**Connects:** uses the MySQL client tools; `backend/SmartRation/scripts/reset_database.py` calls
`backup.ps1` before any reset. Details: [../../docs/database/BACKUP_RESTORE.md](../../docs/database/BACKUP_RESTORE.md).
