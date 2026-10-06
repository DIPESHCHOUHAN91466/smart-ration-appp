-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0007_user_totp).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Downgrade 0007_user_totp -> 0006_password_reset_codes, MySQL 8. Prefer `alembic downgrade 0006_password_reset_codes`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running downgrade 0007_user_totp -> 0006_password_reset_codes

ALTER TABLE `Users` DROP COLUMN `TotpLastStep`;

ALTER TABLE `Users` DROP COLUMN `TotpEnabledAt`;

ALTER TABLE `Users` DROP COLUMN `TotpSecret`;

UPDATE alembic_version SET version_num='0006_password_reset_codes' WHERE alembic_version.version_num = '0007_user_totp';
