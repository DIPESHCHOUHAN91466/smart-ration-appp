-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0004_grievances).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Downgrade 0004_grievances -> 0003_stock_movement_keys, MySQL 8. Prefer `alembic downgrade 0003_stock_movement_keys`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running downgrade 0004_grievances -> 0003_stock_movement_keys

DROP TABLE `Grievances`;

UPDATE alembic_version SET version_num='0003_stock_movement_keys' WHERE alembic_version.version_num = '0004_grievances';
