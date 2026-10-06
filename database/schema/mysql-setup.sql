-- One-time MySQL setup for Smart Ration (run as root in MySQL Workbench or the mysql CLI). Creates the
-- database and three least-privilege accounts, all restricted to connections from this machine:
--   smartration_migrator - changes the schema: migrations and the setup scripts only (MIGRATION_DATABASE_URL)
--   smartration_app      - the running API: reads and writes rows, cannot create, alter or drop anything (DATABASE_URL)
--   smartration_ai       - the Python AI service: READ-ONLY (ai/.env)
--
-- Replace the CHANGE_ME passwords before running, then put the same values in backend/SmartRation/.env and
-- ai/.env (never commit them). An existing installation whose smartration_app still has ALL PRIVILEGES:
-- run database/schema/mysql-least-privilege.sql instead.

CREATE DATABASE IF NOT EXISTS smartration CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'smartration_migrator'@'localhost' IDENTIFIED BY 'CHANGE_ME_MIGRATOR_PASSWORD';
GRANT ALL PRIVILEGES ON smartration.* TO 'smartration_migrator'@'localhost';

CREATE USER IF NOT EXISTS 'smartration_app'@'localhost' IDENTIFIED BY 'CHANGE_ME_APP_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE ON smartration.* TO 'smartration_app'@'localhost';

CREATE USER IF NOT EXISTS 'smartration_ai'@'localhost' IDENTIFIED BY 'CHANGE_ME_AI_PASSWORD';
GRANT SELECT ON smartration.* TO 'smartration_ai'@'localhost';

FLUSH PRIVILEGES;
