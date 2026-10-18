-- Staging accounts on the Azure MySQL server smartration-ai (2026-10-18). Run ONCE as the server admin in MySQL
-- Workbench (keep "Stop script execution on errors" ON, the default), after adding your current IP in
-- Azure Portal -> smartration-ai -> Networking. Remove that IP rule afterwards.
--
-- 1. Type two NEW, different passwords below (at least 16 characters; letters, digits, - and _ only, so they need no
--    escaping in a URL). Never reuse a production or old password. Do not save this file with them in it.
-- 2. Run the whole script. If a password is still CHANGE_ME, too short, or both are the same, it STOPS at the guard
--    with error 1242 ("Subquery returns more than 1 row") before creating anything.
--
-- Both accounts reach ONLY the database smartration_staging - never the production database smartration - and only
-- over TLS. Nothing here drops, truncates or changes production databases or accounts.

SET @migrator_password = 'CHANGE_ME';   -- smartration_stg_migrator: migrations and seeding at start-up
SET @app_password      = 'CHANGE_ME';   -- smartration_stg_app: day-to-day account, rows only

-- Guard: stops the script unless both passwords were replaced properly.
SELECT IF(@migrator_password LIKE 'CHANGE_ME%' OR @app_password LIKE 'CHANGE_ME%'
          OR CHAR_LENGTH(@migrator_password) < 16 OR CHAR_LENGTH(@app_password) < 16
          OR @migrator_password = @app_password
          OR @migrator_password NOT REGEXP '^[A-Za-z0-9_-]+$' OR @app_password NOT REGEXP '^[A-Za-z0-9_-]+$',
          (SELECT 1 UNION ALL SELECT 2),   -- an error on purpose: the script stops here
          'passwords accepted') AS guard;

-- Migrations and seeding (RUN_DB_SETUP / RUN_DB_SEED at start-up): may change tables in smartration_staging only.
SET @sql = CONCAT("CREATE USER IF NOT EXISTS 'smartration_stg_migrator'@'%' IDENTIFIED BY ", QUOTE(@migrator_password), " REQUIRE SSL");
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;
GRANT ALL PRIVILEGES ON smartration_staging.* TO 'smartration_stg_migrator'@'%';

-- Day-to-day runtime account: read and write rows only, no schema changes.
SET @sql = CONCAT("CREATE USER IF NOT EXISTS 'smartration_stg_app'@'%' IDENTIFIED BY ", QUOTE(@app_password), " REQUIRE SSL");
PREPARE s FROM @sql; EXECUTE s; DEALLOCATE PREPARE s;
GRANT SELECT, INSERT, UPDATE, DELETE ON smartration_staging.* TO 'smartration_stg_app'@'%';

-- Forget the passwords in this session.
SET @migrator_password = NULL, @app_password = NULL, @sql = NULL;

-- Check: each account must list only USAGE plus smartration_staging (nothing on smartration or *.*).
SHOW GRANTS FOR 'smartration_stg_migrator'@'%';
SHOW GRANTS FOR 'smartration_stg_app'@'%';

-- Undo (removes staging access completely):
-- DROP USER 'smartration_stg_migrator'@'%'; DROP USER 'smartration_stg_app'@'%';
