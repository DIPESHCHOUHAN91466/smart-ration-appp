-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0005_audit_user_time_index).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Upgrade 0004_grievances -> 0005_audit_user_time_index, MySQL 8. Prefer `alembic upgrade 0005_audit_user_time_index`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running upgrade 0004_grievances -> 0005_audit_user_time_index

CREATE INDEX `IX_AuditLogs_UserId_CreatedAt` ON `AuditLogs` (`UserId`, `CreatedAt`);

UPDATE alembic_version SET version_num='0005_audit_user_time_index' WHERE alembic_version.version_num = '0004_grievances';
