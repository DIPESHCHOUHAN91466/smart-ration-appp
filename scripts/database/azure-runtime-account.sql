-- Least privilege on Azure MySQL (security N8): a rows-only account for the RUNNING app.
-- The existing account (the one in DATABASE_URL today) keeps its rights and becomes MIGRATION_DATABASE_URL:
-- only the start-up migration step uses it. Run this as the server ADMIN (airationmitrahsd2c) in MySQL Workbench
-- or Azure Cloud Shell, after replacing CHOOSE-A-LONG-RANDOM-PASSWORD in the editor. Do NOT save the file with
-- the password in it, and do not commit it.

CREATE USER IF NOT EXISTS 'smartration_runtime'@'%' IDENTIFIED BY 'CHOOSE-A-LONG-RANDOM-PASSWORD' REQUIRE SSL;
GRANT SELECT, INSERT, UPDATE, DELETE ON `smartration`.* TO 'smartration_runtime'@'%';

-- Check: exactly these four rights, on smartration only.
SHOW GRANTS FOR 'smartration_runtime'@'%';

-- Undo (after switching the app back with set-runtime-db-account.ps1 -Undo):
-- DROP USER 'smartration_runtime'@'%';
