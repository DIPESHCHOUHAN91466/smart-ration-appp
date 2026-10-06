-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0006_password_reset_codes).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Upgrade 0005_audit_user_time_index -> 0006_password_reset_codes, MySQL 8. Prefer `alembic upgrade 0006_password_reset_codes`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running upgrade 0005_audit_user_time_index -> 0006_password_reset_codes

CREATE TABLE `PasswordResetCodes` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `UserId` INTEGER NOT NULL,
    `CodeHash` VARCHAR(64) NOT NULL,
    `AttemptCount` INTEGER NOT NULL,
    `MaxAttempts` INTEGER NOT NULL,
    `Status` INTEGER NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    `ExpiresAt` DATETIME(6) NOT NULL,
    `UsedAt` DATETIME(6),
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_PasswordResetCodes_Users_UserId` FOREIGN KEY(`UserId`) REFERENCES `Users` (`Id`) ON DELETE CASCADE
);

CREATE INDEX `IX_PasswordResetCodes_UserId_CreatedAt` ON `PasswordResetCodes` (`UserId`, `CreatedAt`);

UPDATE alembic_version SET version_num='0006_password_reset_codes' WHERE alembic_version.version_num = '0005_audit_user_time_index';
