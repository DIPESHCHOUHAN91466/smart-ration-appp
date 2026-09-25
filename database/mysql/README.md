# database/mysql — backup and restore

**What:** PowerShell scripts that back up and restore the `smartration` database. **Why:** every
schema change, restore or reset starts with a backup; restores must never lose the current data.
**Belongs here:** `backup.ps1`, `restore.ps1`, and `backups/` (git-ignored output).
**Doesn't:** schema or migrations (Alembic, in the Python backend), real credentials.
**Run:**
```
$env:SMARTRATION_DB_USER = "smartration_app"; $env:SMARTRATION_DB_PASSWORD = "<password>"
.\database\mysql\backup.ps1                                          # → backups\smartration_<timestamp>.sql.gz + .sha256
.\database\mysql\restore.ps1 -BackupFile <file> -Confirm RESTORE_SMARTRATION   # verifies checksum, backs up first
```
**Connects:** uses the MySQL client tools; `backend/SmartRation.Python/scripts/reset_database.py` calls
`backup.ps1` before any reset. Details: [../../docs/database/BACKUP_RESTORE.md](../../docs/database/BACKUP_RESTORE.md).
