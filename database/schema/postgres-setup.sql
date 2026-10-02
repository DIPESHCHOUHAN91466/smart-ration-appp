-- Smart Ration HSD2C — one-time PostgreSQL setup (run as the 'postgres' superuser).
--
--   1. Copy this file to database\postgres-setup.local.sql   (*.local.sql is git-ignored)
--   2. In the copy, replace both CHANGE_ME_... passwords with long random ones.
--   3. Run:  & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -f database\postgres-setup.local.sql
--   4. Put the app login into backend\SmartRation\.env:
--        DATABASE_URL=postgresql+psycopg://smartration_app:<app password>@localhost:5432/smartration
--      and the read-only login into ai\.env:
--        SMARTRATION_AI_DB_URL=postgresql+psycopg://smartration_ai:<ai password>@localhost:5432/smartration
--
-- Creates:
--   smartration_app   owns both databases; the Python API reads and writes with it (tables are created by
--                     Alembic: backend\SmartRation\scripts\setup_database.py)
--   smartration_ai    READ-ONLY login for the AI analytics service (SELECT only, also on future tables)
--   smartration       the application database
--   smartration_test  a separate database for the automated test suites (never the real one)
-- Safe to re-run: existing logins and databases are left alone.

SELECT 'CREATE ROLE smartration_app LOGIN PASSWORD ''CHANGE_ME_APP_PASSWORD'''
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'smartration_app')\gexec

SELECT 'CREATE ROLE smartration_ai LOGIN PASSWORD ''CHANGE_ME_AI_PASSWORD'''
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'smartration_ai')\gexec

SELECT 'CREATE DATABASE smartration OWNER smartration_app ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smartration')\gexec

SELECT 'CREATE DATABASE smartration_test OWNER smartration_app ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smartration_test')\gexec

-- Read-only access for the AI service, including tables Alembic creates later.
\connect smartration
GRANT CONNECT ON DATABASE smartration TO smartration_ai;
GRANT USAGE ON SCHEMA public TO smartration_ai;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO smartration_ai;
ALTER DEFAULT PRIVILEGES FOR ROLE smartration_app IN SCHEMA public GRANT SELECT ON TABLES TO smartration_ai;
