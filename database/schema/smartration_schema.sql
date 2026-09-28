-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations (Alembic).
-- Regenerate: cd backend/SmartRation; .venv\Scripts\python scripts\export_schema_sql.py
-- MySQL 8 (tables use the database defaults: InnoDB, utf8mb4). Apply schema changes with `alembic upgrade head`, never with this file.

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_initial

CREATE TABLE `AIAlerts` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `ShopId` INTEGER,
    `BeneficiaryId` INTEGER,
    `AlertType` VARCHAR(64) NOT NULL,
    `Severity` INTEGER NOT NULL,
    `Description` LONGTEXT NOT NULL,
    `Status` INTEGER NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    `ResolvedAt` DATETIME(6),
    `Source` VARCHAR(32) NOT NULL DEFAULT 'RULES',
    `Title` VARCHAR(200),
    `RationType` INTEGER,
    `Score` DOUBLE,
    `RecommendedAction` VARCHAR(500),
    `DedupKey` VARCHAR(128),
    `MetadataJson` LONGTEXT,
    `DetectedAt` DATETIME(6),
    `LastSeenAt` DATETIME(6),
    `ResolvedByUserId` INTEGER,
    `ResolutionNote` VARCHAR(500),
    PRIMARY KEY (`Id`)
);

CREATE INDEX `IX_AIAlerts_DedupKey_Status` ON `AIAlerts` (`DedupKey`, `Status`);

CREATE INDEX `IX_AIAlerts_ShopId_Status` ON `AIAlerts` (`ShopId`, `Status`);

CREATE TABLE `AIInsights` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `EntityType` LONGTEXT NOT NULL,
    `EntityId` INTEGER,
    `InsightType` LONGTEXT NOT NULL,
    `RiskLevel` INTEGER NOT NULL,
    `Score` DOUBLE NOT NULL,
    `Explanation` LONGTEXT NOT NULL,
    `Recommendation` LONGTEXT NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`)
);

CREATE TABLE `AuditLogs` (
    `Id` BIGINT NOT NULL AUTO_INCREMENT,
    `UserId` INTEGER,
    `Action` LONGTEXT NOT NULL,
    `EntityName` LONGTEXT NOT NULL,
    `EntityId` LONGTEXT,
    `IpAddress` LONGTEXT,
    `Details` LONGTEXT,
    `Role` VARCHAR(32),
    `Result` VARCHAR(16),
    `CreatedAt` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`)
);

CREATE TABLE `RationItems` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `RationType` INTEGER NOT NULL,
    `Name` LONGTEXT NOT NULL,
    `VernacularName` LONGTEXT NOT NULL,
    `Unit` LONGTEXT NOT NULL,
    `StandardQuotaPerBooking` NUMERIC(65, 30) NOT NULL,
    `IsActive` BOOL NOT NULL,
    PRIMARY KEY (`Id`)
);

CREATE UNIQUE INDEX `IX_RationItems_RationType` ON `RationItems` (`RationType`);

CREATE TABLE `RationSchemes` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `SchemeCode` VARCHAR(255) NOT NULL,
    `Name` LONGTEXT NOT NULL,
    `Description` LONGTEXT NOT NULL,
    `IsActive` BOOL NOT NULL,
    PRIMARY KEY (`Id`)
);

CREATE UNIQUE INDEX `IX_RationSchemes_SchemeCode` ON `RationSchemes` (`SchemeCode`);

CREATE TABLE `RationShops` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `ShopName` LONGTEXT NOT NULL,
    `ShopCode` VARCHAR(255) NOT NULL,
    `Address` LONGTEXT NOT NULL,
    `District` LONGTEXT NOT NULL,
    `State` LONGTEXT NOT NULL,
    `Taluka` LONGTEXT,
    `Village` LONGTEXT,
    `Latitude` DOUBLE NOT NULL,
    `Longitude` DOUBLE NOT NULL,
    `IsActive` BOOL NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`)
);

CREATE UNIQUE INDEX `IX_RationShops_ShopCode` ON `RationShops` (`ShopCode`);

CREATE TABLE `VerificationAuditLogs` (
    `Id` BIGINT NOT NULL AUTO_INCREMENT,
    `VerificationReference` LONGTEXT,
    `TokenNumber` LONGTEXT,
    `BeneficiaryId` INTEGER,
    `ShopId` INTEGER,
    `Action` INTEGER NOT NULL,
    `VerificationMethod` LONGTEXT NOT NULL,
    `Status` LONGTEXT NOT NULL,
    `Reason` LONGTEXT,
    `OperatorId` INTEGER,
    `DeviceInfo` LONGTEXT,
    `IpAddress` LONGTEXT,
    `Timestamp` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`)
);

CREATE TABLE `Families` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `FamilyCode` VARCHAR(255) NOT NULL,
    `RationShopId` INTEGER NOT NULL,
    `RationSchemeId` INTEGER NOT NULL,
    `DataSource` LONGTEXT NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_Families_RationSchemes_RationSchemeId` FOREIGN KEY(`RationSchemeId`) REFERENCES `RationSchemes` (`Id`) ON DELETE RESTRICT,
    CONSTRAINT `FK_Families_RationShops_RationShopId` FOREIGN KEY(`RationShopId`) REFERENCES `RationShops` (`Id`) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX `IX_Families_FamilyCode` ON `Families` (`FamilyCode`);

CREATE INDEX `IX_Families_RationSchemeId` ON `Families` (`RationSchemeId`);

CREATE INDEX `IX_Families_RationShopId` ON `Families` (`RationShopId`);

CREATE TABLE `Inventory` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `RationShopId` INTEGER NOT NULL,
    `RationType` INTEGER NOT NULL,
    `AvailableQuantity` NUMERIC(65, 30) NOT NULL,
    `AllocatedQuantity` NUMERIC(65, 30) NOT NULL,
    `MinimumStockLevel` NUMERIC(65, 30) NOT NULL,
    `UpdatedAt` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_Inventory_RationShops_RationShopId` FOREIGN KEY(`RationShopId`) REFERENCES `RationShops` (`Id`) ON DELETE CASCADE
);

CREATE UNIQUE INDEX `IX_Inventory_RationShopId_RationType` ON `Inventory` (`RationShopId`, `RationType`);

CREATE TABLE `InventoryMovements` (
    `Id` BIGINT NOT NULL AUTO_INCREMENT,
    `RationShopId` INTEGER NOT NULL,
    `RationType` INTEGER NOT NULL,
    `MovementType` INTEGER NOT NULL,
    `Quantity` NUMERIC(65, 30) NOT NULL,
    `BalanceAfter` NUMERIC(65, 30) NOT NULL,
    `Reference` VARCHAR(64),
    `Note` VARCHAR(256),
    `RecordedByUserId` INTEGER,
    `CreatedAt` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_InventoryMovements_RationShops_RationShopId` FOREIGN KEY(`RationShopId`) REFERENCES `RationShops` (`Id`) ON DELETE RESTRICT
);

CREATE INDEX `IX_InventoryMovements_RationShopId_RationType_CreatedAt` ON `InventoryMovements` (`RationShopId`, `RationType`, `CreatedAt`);

CREATE TABLE `SchemeEntitlementItems` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `RationSchemeId` INTEGER NOT NULL,
    `RationType` INTEGER NOT NULL,
    `QuotaPerEligibleMemberPerMonth` NUMERIC(65, 30) NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_SchemeEntitlementItems_RationSchemes_RationSchemeId` FOREIGN KEY(`RationSchemeId`) REFERENCES `RationSchemes` (`Id`) ON DELETE CASCADE
);

CREATE UNIQUE INDEX `IX_SchemeEntitlementItems_RationSchemeId_RationType` ON `SchemeEntitlementItems` (`RationSchemeId`, `RationType`);

CREATE TABLE `TimeSlots` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `RationShopId` INTEGER NOT NULL,
    `SlotDate` DATETIME(6) NOT NULL,
    `StartTime` TIME(6) NOT NULL,
    `EndTime` TIME(6) NOT NULL,
    `Capacity` INTEGER NOT NULL,
    `BookedCount` INTEGER NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_TimeSlots_RationShops_RationShopId` FOREIGN KEY(`RationShopId`) REFERENCES `RationShops` (`Id`) ON DELETE CASCADE
);

CREATE INDEX `IX_TimeSlots_RationShopId` ON `TimeSlots` (`RationShopId`);

CREATE TABLE `Users` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `FullName` LONGTEXT NOT NULL,
    `Email` VARCHAR(255) NOT NULL,
    `MobileNumber` VARCHAR(255) NOT NULL,
    `PasswordHash` LONGTEXT NOT NULL,
    `Role` INTEGER NOT NULL,
    `IsActive` BOOL NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    `RationShopId` INTEGER,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_Users_RationShops_RationShopId` FOREIGN KEY(`RationShopId`) REFERENCES `RationShops` (`Id`) ON DELETE SET NULL
);

CREATE UNIQUE INDEX `IX_Users_Email` ON `Users` (`Email`);

CREATE UNIQUE INDEX `IX_Users_MobileNumber` ON `Users` (`MobileNumber`);

CREATE INDEX `IX_Users_RationShopId` ON `Users` (`RationShopId`);

CREATE TABLE `Beneficiaries` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `BeneficiaryCode` VARCHAR(255) NOT NULL,
    `Address` LONGTEXT NOT NULL,
    `Gender` INTEGER NOT NULL,
    `DateOfBirth` DATETIME(6) NOT NULL,
    `Village` LONGTEXT NOT NULL,
    `District` LONGTEXT NOT NULL,
    `State` LONGTEXT NOT NULL,
    `Pincode` LONGTEXT NOT NULL,
    `ProfilePhotoUrl` LONGTEXT,
    `UserId` INTEGER NOT NULL,
    `FamilyId` INTEGER NOT NULL,
    `IsActive` BOOL NOT NULL,
    `IsBlocked` BOOL NOT NULL,
    `DataSource` LONGTEXT NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_Beneficiaries_Families_FamilyId` FOREIGN KEY(`FamilyId`) REFERENCES `Families` (`Id`) ON DELETE RESTRICT,
    CONSTRAINT `FK_Beneficiaries_Users_UserId` FOREIGN KEY(`UserId`) REFERENCES `Users` (`Id`) ON DELETE CASCADE
);

CREATE UNIQUE INDEX `IX_Beneficiaries_BeneficiaryCode` ON `Beneficiaries` (`BeneficiaryCode`);

CREATE INDEX `IX_Beneficiaries_FamilyId` ON `Beneficiaries` (`FamilyId`);

CREATE UNIQUE INDEX `IX_Beneficiaries_UserId` ON `Beneficiaries` (`UserId`);

CREATE TABLE `FamilyMembers` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `FamilyId` INTEGER NOT NULL,
    `FullName` LONGTEXT NOT NULL,
    `Age` INTEGER NOT NULL,
    `Relationship` INTEGER NOT NULL,
    `Eligibility` INTEGER NOT NULL,
    `DataSource` LONGTEXT NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_FamilyMembers_Families_FamilyId` FOREIGN KEY(`FamilyId`) REFERENCES `Families` (`Id`) ON DELETE CASCADE
);

CREATE INDEX `IX_FamilyMembers_FamilyId` ON `FamilyMembers` (`FamilyId`);

CREATE TABLE `Notifications` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `UserId` INTEGER NOT NULL,
    `Type` INTEGER NOT NULL,
    `Title` LONGTEXT NOT NULL,
    `Message` LONGTEXT NOT NULL,
    `IsRead` BOOL NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_Notifications_Users_UserId` FOREIGN KEY(`UserId`) REFERENCES `Users` (`Id`) ON DELETE CASCADE
);

CREATE INDEX `IX_Notifications_UserId` ON `Notifications` (`UserId`);

CREATE TABLE `RefreshTokens` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `UserId` INTEGER NOT NULL,
    `TokenHash` VARCHAR(255) NOT NULL,
    `ExpiresAt` DATETIME(6) NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    `RevokedAt` DATETIME(6),
    `ReplacedByTokenHash` LONGTEXT,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_RefreshTokens_Users_UserId` FOREIGN KEY(`UserId`) REFERENCES `Users` (`Id`) ON DELETE CASCADE
);

CREATE UNIQUE INDEX `IX_RefreshTokens_TokenHash` ON `RefreshTokens` (`TokenHash`);

CREATE INDEX `IX_RefreshTokens_UserId` ON `RefreshTokens` (`UserId`);

CREATE TABLE `Tokens` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `TokenNumber` VARCHAR(255) NOT NULL,
    `UserId` INTEGER NOT NULL,
    `RationShopId` INTEGER NOT NULL,
    `TimeSlotId` INTEGER NOT NULL,
    `Status` INTEGER NOT NULL,
    `QRCodeValue` LONGTEXT,
    `CreatedAt` DATETIME(6) NOT NULL,
    `CollectedAt` DATETIME(6),
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_Tokens_RationShops_RationShopId` FOREIGN KEY(`RationShopId`) REFERENCES `RationShops` (`Id`) ON DELETE RESTRICT,
    CONSTRAINT `FK_Tokens_TimeSlots_TimeSlotId` FOREIGN KEY(`TimeSlotId`) REFERENCES `TimeSlots` (`Id`) ON DELETE RESTRICT,
    CONSTRAINT `FK_Tokens_Users_UserId` FOREIGN KEY(`UserId`) REFERENCES `Users` (`Id`) ON DELETE RESTRICT
);

CREATE INDEX `IX_Tokens_RationShopId` ON `Tokens` (`RationShopId`);

CREATE INDEX `IX_Tokens_TimeSlotId` ON `Tokens` (`TimeSlotId`);

CREATE UNIQUE INDEX `IX_Tokens_TokenNumber` ON `Tokens` (`TokenNumber`);

CREATE INDEX `IX_Tokens_UserId` ON `Tokens` (`UserId`);

CREATE TABLE `AadhaarVerifications` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `BeneficiaryId` INTEGER NOT NULL,
    `AadhaarReferenceId` LONGTEXT NOT NULL,
    `AadhaarMasked` LONGTEXT NOT NULL,
    `Status` INTEGER NOT NULL,
    `VerificationDate` DATETIME(6),
    `VerificationSource` LONGTEXT NOT NULL,
    `VerificationMode` LONGTEXT NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_AadhaarVerifications_Beneficiaries_BeneficiaryId` FOREIGN KEY(`BeneficiaryId`) REFERENCES `Beneficiaries` (`Id`) ON DELETE CASCADE
);

CREATE UNIQUE INDEX `IX_AadhaarVerifications_BeneficiaryId` ON `AadhaarVerifications` (`BeneficiaryId`);

CREATE TABLE `MobileVerifications` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `BeneficiaryId` INTEGER NOT NULL,
    `MobileMasked` LONGTEXT NOT NULL,
    `Status` INTEGER NOT NULL,
    `VerifiedAt` DATETIME(6),
    `VerificationSource` LONGTEXT NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_MobileVerifications_Beneficiaries_BeneficiaryId` FOREIGN KEY(`BeneficiaryId`) REFERENCES `Beneficiaries` (`Id`) ON DELETE CASCADE
);

CREATE UNIQUE INDEX `IX_MobileVerifications_BeneficiaryId` ON `MobileVerifications` (`BeneficiaryId`);

CREATE TABLE `OtpVerifications` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `BeneficiaryId` INTEGER NOT NULL,
    `RequestedByUserId` INTEGER NOT NULL,
    `OtpHash` LONGTEXT NOT NULL,
    `AttemptCount` INTEGER NOT NULL,
    `MaxAttempts` INTEGER NOT NULL,
    `Status` INTEGER NOT NULL,
    `CreatedAt` DATETIME(6) NOT NULL,
    `ExpiresAt` DATETIME(6) NOT NULL,
    `VerifiedAt` DATETIME(6),
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_OtpVerifications_Beneficiaries_BeneficiaryId` FOREIGN KEY(`BeneficiaryId`) REFERENCES `Beneficiaries` (`Id`) ON DELETE CASCADE
);

CREATE INDEX `IX_OtpVerifications_BeneficiaryId` ON `OtpVerifications` (`BeneficiaryId`);

CREATE TABLE `PassbookVerifications` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `BeneficiaryId` INTEGER NOT NULL,
    `PassbookNumber` LONGTEXT NOT NULL,
    `Status` LONGTEXT NOT NULL,
    `VerificationStatus` INTEGER NOT NULL,
    `LastUpdated` DATETIME(6) NOT NULL,
    `VerificationSource` LONGTEXT NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_PassbookVerifications_Beneficiaries_BeneficiaryId` FOREIGN KEY(`BeneficiaryId`) REFERENCES `Beneficiaries` (`Id`) ON DELETE CASCADE
);

CREATE UNIQUE INDEX `IX_PassbookVerifications_BeneficiaryId` ON `PassbookVerifications` (`BeneficiaryId`);

CREATE TABLE `RationCollections` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `CollectionCode` VARCHAR(255) NOT NULL,
    `TokenId` INTEGER NOT NULL,
    `BeneficiaryId` INTEGER NOT NULL,
    `RationShopId` INTEGER NOT NULL,
    `OperatorUserId` INTEGER NOT NULL,
    `VerificationMethod` LONGTEXT NOT NULL,
    `CollectedAt` DATETIME(6) NOT NULL,
    `IdempotencyKey` VARCHAR(64),
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_RationCollections_Beneficiaries_BeneficiaryId` FOREIGN KEY(`BeneficiaryId`) REFERENCES `Beneficiaries` (`Id`) ON DELETE RESTRICT,
    CONSTRAINT `FK_RationCollections_RationShops_RationShopId` FOREIGN KEY(`RationShopId`) REFERENCES `RationShops` (`Id`) ON DELETE RESTRICT,
    CONSTRAINT `FK_RationCollections_Tokens_TokenId` FOREIGN KEY(`TokenId`) REFERENCES `Tokens` (`Id`) ON DELETE RESTRICT
);

CREATE INDEX `IX_RationCollections_BeneficiaryId` ON `RationCollections` (`BeneficiaryId`);

CREATE UNIQUE INDEX `IX_RationCollections_CollectionCode` ON `RationCollections` (`CollectionCode`);

CREATE UNIQUE INDEX `IX_RationCollections_IdempotencyKey` ON `RationCollections` (`IdempotencyKey`);

CREATE INDEX `IX_RationCollections_RationShopId` ON `RationCollections` (`RationShopId`);

CREATE UNIQUE INDEX `IX_RationCollections_TokenId` ON `RationCollections` (`TokenId`);

CREATE TABLE `TokenItems` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `TokenId` INTEGER NOT NULL,
    `RationType` INTEGER NOT NULL,
    `Quantity` NUMERIC(65, 30) NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_TokenItems_Tokens_TokenId` FOREIGN KEY(`TokenId`) REFERENCES `Tokens` (`Id`) ON DELETE CASCADE
);

CREATE INDEX `IX_TokenItems_TokenId` ON `TokenItems` (`TokenId`);

CREATE TABLE `RationCollectionItems` (
    `Id` INTEGER NOT NULL AUTO_INCREMENT,
    `RationCollectionId` INTEGER NOT NULL,
    `RationType` INTEGER NOT NULL,
    `Quantity` NUMERIC(65, 30) NOT NULL,
    PRIMARY KEY (`Id`),
    CONSTRAINT `FK_RationCollectionItems_RationCollections_RationCollectionId` FOREIGN KEY(`RationCollectionId`) REFERENCES `RationCollections` (`Id`) ON DELETE CASCADE
);

CREATE INDEX `IX_RationCollectionItems_RationCollectionId` ON `RationCollectionItems` (`RationCollectionId`);

INSERT INTO alembic_version (version_num) VALUES ('0001_initial');
