-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0006_password_reset_codes).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Downgrade 0006_password_reset_codes -> 0005_audit_user_time_index, MySQL 8. Prefer `alembic downgrade 0005_audit_user_time_index`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running downgrade 0006_password_reset_codes -> 0005_audit_user_time_index

DROP TABLE `PasswordResetCodes`;

UPDATE alembic_version SET version_num='0005_audit_user_time_index' WHERE alembic_version.version_num = '0006_password_reset_codes';
