-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0003_stock_movement_keys).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Downgrade 0003_stock_movement_keys -> 0002_family_member_gender, MySQL 8. Prefer `alembic downgrade 0002_family_member_gender`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running downgrade 0003_stock_movement_keys -> 0002_family_member_gender

DROP INDEX `IX_InventoryMovements_IdempotencyKey` ON `InventoryMovements`;

ALTER TABLE `InventoryMovements` DROP COLUMN `IdempotencyKey`;

UPDATE alembic_version SET version_num='0002_family_member_gender' WHERE alembic_version.version_num = '0003_stock_movement_keys';
