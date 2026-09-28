-- One-time MySQL setup for Smart Ration (run as root in MySQL Workbench or
-- the mysql CLI). Creates the application database plus two least-privilege
-- accounts, both restricted to connections from this machine:
--   smartration_app — used by the .NET backend (owns the schema, runs migrations)
--   smartration_ai  — used by the Python AI service (READ-ONLY)
--
-- Replace the CHANGE_ME passwords before running, then put the same values
-- in .NET user-secrets / backend/SmartRation.AI/.env (never commit them).

CREATE DATABASE IF NOT EXISTS smartration CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'smartration_app'@'localhost' IDENTIFIED BY 'CHANGE_ME_APP_PASSWORD';
GRANT ALL PRIVILEGES ON smartration.* TO 'smartration_app'@'localhost';

CREATE USER IF NOT EXISTS 'smartration_ai'@'localhost' IDENTIFIED BY 'CHANGE_ME_AI_PASSWORD';
GRANT SELECT ON smartration.* TO 'smartration_ai'@'localhost';

FLUSH PRIVILEGES;
