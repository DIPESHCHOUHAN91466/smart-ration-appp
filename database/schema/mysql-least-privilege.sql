-- Security N8: move an EXISTING installation to least privilege (run as root, after a backup:
-- scripts/database/backup.ps1). Changes no data and no table; only who may change the schema.
--
-- Before: smartration_app (the running API) has ALL PRIVILEGES, so a bug or an injection could drop tables.
-- After:  smartration_migrator owns the schema (migrations, setup scripts);
--         smartration_app may only SELECT, INSERT, UPDATE and DELETE rows.
--
-- 1. Replace CHANGE_ME_MIGRATOR_PASSWORD, then run this file as root.
-- 2. In backend/SmartRation/.env add
--      MIGRATION_DATABASE_URL=mysql+pymysql://smartration_migrator:<that password>@localhost:3306/smartration?charset=utf8mb4
--    (DATABASE_URL stays as it is), and restart the API.
-- 3. Check: from backend/SmartRation run  .venv\Scripts\python scripts\verify_database.py  -> DATABASE VERIFICATION PASSED
-- Undo (back to the old setup): GRANT ALL PRIVILEGES ON smartration.* TO 'smartration_app'@'localhost';

CREATE USER IF NOT EXISTS 'smartration_migrator'@'localhost' IDENTIFIED BY 'CHANGE_ME_MIGRATOR_PASSWORD';
GRANT ALL PRIVILEGES ON smartration.* TO 'smartration_migrator'@'localhost';

REVOKE ALL PRIVILEGES ON smartration.* FROM 'smartration_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON smartration.* TO 'smartration_app'@'localhost';

FLUSH PRIVILEGES;
SHOW GRANTS FOR 'smartration_app'@'localhost';
