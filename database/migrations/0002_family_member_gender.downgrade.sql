-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0002_family_member_gender).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Downgrade 0002_family_member_gender -> 0001_initial, MySQL 8. Prefer `alembic downgrade 0001_initial`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running downgrade 0002_family_member_gender -> 0001_initial

ALTER TABLE `FamilyMembers` DROP COLUMN `Gender`;

UPDATE alembic_version SET version_num='0001_initial' WHERE alembic_version.version_num = '0002_family_member_gender';
