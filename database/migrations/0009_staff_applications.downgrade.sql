-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0009_staff_applications).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Downgrade 0009_staff_applications -> 0007_user_totp, MySQL 8. Prefer `alembic downgrade 0007_user_totp`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running downgrade 0009_staff_applications -> 0007_user_totp

DROP TABLE `StaffApplications`;

UPDATE alembic_version SET version_num='0007_user_totp' WHERE alembic_version.version_num = '0009_staff_applications';
