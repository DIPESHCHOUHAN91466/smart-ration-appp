-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0009_staff_applications).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Upgrade 0007_user_totp -> 0009_staff_applications, MySQL 8. Prefer `alembic upgrade 0009_staff_applications`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running upgrade 0007_user_totp -> 0009_staff_applications

CREATE TABLE `StaffApplications` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `UserId` INTEGER NOT NULL,
    `RequestedRole` INTEGER NOT NULL,
    `RationShopId` INTEGER,
    `Office` VARCHAR(200),
    `Designation` VARCHAR(120) NOT NULL,
    `ProofReference` VARCHAR(120) NOT NULL,
    `Status` INTEGER NOT NULL,
    `DecidedByUserId` INTEGER,
    `DecisionReason` VARCHAR(500),
    `CreatedAt` DATETIME(6) NOT NULL,
    `DecidedAt` DATETIME(6),
    PRIMARY KEY (`Id`),
    CONSTRAINT `CK_StaffApplications_RequestedRole` CHECK (RequestedRole IN (2, 3)),
    CONSTRAINT `CK_StaffApplications_Status` CHECK (Status IN (1, 2, 3, 4)),
    CONSTRAINT `FK_StaffApplications_Users_UserId` FOREIGN KEY(`UserId`) REFERENCES `Users` (`Id`) ON DELETE CASCADE,
    CONSTRAINT `FK_StaffApplications_RationShops_RationShopId` FOREIGN KEY(`RationShopId`) REFERENCES `RationShops` (`Id`) ON DELETE RESTRICT,
    CONSTRAINT `FK_StaffApplications_Users_DecidedByUserId` FOREIGN KEY(`DecidedByUserId`) REFERENCES `Users` (`Id`) ON DELETE SET NULL
);

CREATE INDEX `IX_StaffApplications_UserId_Status` ON `StaffApplications` (`UserId`, `Status`);

CREATE INDEX `IX_StaffApplications_Status_CreatedAt` ON `StaffApplications` (`Status`, `CreatedAt`);

UPDATE alembic_version SET version_num='0009_staff_applications' WHERE alembic_version.version_num = '0007_user_totp';
