-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0005_audit_user_time_index).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Downgrade 0005_audit_user_time_index -> 0004_grievances, MySQL 8. Prefer `alembic downgrade 0004_grievances`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running downgrade 0005_audit_user_time_index -> 0004_grievances

DROP INDEX `IX_AuditLogs_UserId_CreatedAt` ON `AuditLogs`;

UPDATE alembic_version SET version_num='0004_grievances' WHERE alembic_version.version_num = '0005_audit_user_time_index';
