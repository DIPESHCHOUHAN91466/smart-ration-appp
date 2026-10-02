-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision 0004_grievances).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- Upgrade 0003_stock_movement_keys -> 0004_grievances, MySQL 8. Prefer `alembic upgrade 0004_grievances`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

-- Running upgrade 0003_stock_movement_keys -> 0004_grievances

CREATE TABLE `Grievances` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `ReferenceNumber` VARCHAR(32) NOT NULL,
    `UserId` INTEGER NOT NULL,
    `RationShopId` INTEGER,
    `Category` INTEGER NOT NULL,
    `RationType` INTEGER,
    `Description` VARCHAR(1000) NOT NULL,
    `Status` INTEGER NOT NULL,
    `Source` VARCHAR(16) NOT NULL DEFAULT 'APP',
    `IdempotencyKey` VARCHAR(64),
    `ResolutionNote` VARCHAR(500),
    `ResolvedByUserId` INTEGER,
    `CreatedAt` DATETIME(6) NOT NULL,
    `UpdatedAt` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_Grievances_Users_UserId` FOREIGN KEY(`UserId`) REFERENCES `Users` (`Id`) ON DELETE RESTRICT,
    CONSTRAINT `FK_Grievances_RationShops_RationShopId` FOREIGN KEY(`RationShopId`) REFERENCES `RationShops` (`Id`) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX `IX_Grievances_ReferenceNumber` ON `Grievances` (`ReferenceNumber`);

CREATE UNIQUE INDEX `IX_Grievances_IdempotencyKey` ON `Grievances` (`IdempotencyKey`);

CREATE INDEX `IX_Grievances_UserId_CreatedAt` ON `Grievances` (`UserId`, `CreatedAt`);

CREATE INDEX `IX_Grievances_Status_CreatedAt` ON `Grievances` (`Status`, `CreatedAt`);

CREATE INDEX `IX_Grievances_RationShopId_Status` ON `Grievances` (`RationShopId`, `Status`);

UPDATE alembic_version SET version_num='0004_grievances' WHERE alembic_version.version_num = '0003_stock_movement_keys';
