-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0007_user_totp).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Upgrade 0006_password_reset_codes -> 0007_user_totp, MySQL 8. Prefer `alembic upgrade 0007_user_totp`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running upgrade 0006_password_reset_codes -> 0007_user_totp

ALTER TABLE `Users` ADD COLUMN `TotpSecret` VARCHAR(255);

ALTER TABLE `Users` ADD COLUMN `TotpEnabledAt` DATETIME(6);

ALTER TABLE `Users` ADD COLUMN `TotpLastStep` BIGINT;

UPDATE alembic_version SET version_num='0007_user_totp' WHERE alembic_version.version_num = '0006_password_reset_codes';
