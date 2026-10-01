-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0002_family_member_gender).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Upgrade 0001_initial -> 0002_family_member_gender, MySQL 8. Prefer `alembic upgrade 0002_family_member_gender`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running upgrade 0001_initial -> 0002_family_member_gender

ALTER TABLE `FamilyMembers` ADD COLUMN `Gender` INTEGER;

UPDATE FamilyMembers SET Gender = 1 WHERE Relationship = 3 AND Gender IS NULL;

UPDATE FamilyMembers SET Gender = 2 WHERE Relationship = 4 AND Gender IS NULL;

UPDATE FamilyMembers SET Gender = ( SELECT b.Gender FROM Beneficiaries b WHERE b.FamilyId = FamilyMembers.FamilyId ORDER BY b.Id LIMIT 1) WHERE Relationship = 1 AND Gender IS NULL;

UPDATE alembic_version SET version_num='0002_family_member_gender' WHERE alembic_version.version_num = '0001_initial';
