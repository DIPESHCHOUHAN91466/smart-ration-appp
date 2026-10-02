-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0003_stock_movement_keys).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Upgrade 0002_family_member_gender -> 0003_stock_movement_keys, MySQL 8. Prefer `alembic upgrade 0003_stock_movement_keys`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running upgrade 0002_family_member_gender -> 0003_stock_movement_keys

ALTER TABLE `InventoryMovements` ADD COLUMN `IdempotencyKey` VARCHAR(64);

CREATE UNIQUE INDEX `IX_InventoryMovements_IdempotencyKey` ON `InventoryMovements` (`IdempotencyKey`);

UPDATE alembic_version SET version_num='0003_stock_movement_keys' WHERE alembic_version.version_num = '0002_family_member_gender';
