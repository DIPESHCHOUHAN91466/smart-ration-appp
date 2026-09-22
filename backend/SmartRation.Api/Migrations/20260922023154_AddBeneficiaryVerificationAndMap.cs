using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SmartRation.Api.Migrations
{
    /// <inheritdoc />
    public partial class AddBeneficiaryVerificationAndMap : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "Taluka",
                table: "RationShops",
                type: "TEXT",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "Village",
                table: "RationShops",
                type: "TEXT",
                nullable: true);

            migrationBuilder.CreateTable(
                name: "RationSchemes",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    SchemeCode = table.Column<string>(type: "TEXT", nullable: false),
                    Name = table.Column<string>(type: "TEXT", nullable: false),
                    Description = table.Column<string>(type: "TEXT", nullable: false),
                    IsActive = table.Column<bool>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_RationSchemes", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "VerificationAuditLogs",
                columns: table => new
                {
                    Id = table.Column<long>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    VerificationReference = table.Column<string>(type: "TEXT", nullable: true),
                    TokenNumber = table.Column<string>(type: "TEXT", nullable: true),
                    BeneficiaryId = table.Column<int>(type: "INTEGER", nullable: true),
                    ShopId = table.Column<int>(type: "INTEGER", nullable: true),
                    Action = table.Column<int>(type: "INTEGER", nullable: false),
                    VerificationMethod = table.Column<string>(type: "TEXT", nullable: false),
                    Status = table.Column<string>(type: "TEXT", nullable: false),
                    Reason = table.Column<string>(type: "TEXT", nullable: true),
                    OperatorId = table.Column<int>(type: "INTEGER", nullable: true),
                    DeviceInfo = table.Column<string>(type: "TEXT", nullable: true),
                    IpAddress = table.Column<string>(type: "TEXT", nullable: true),
                    Timestamp = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_VerificationAuditLogs", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Families",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    FamilyCode = table.Column<string>(type: "TEXT", nullable: false),
                    RationShopId = table.Column<int>(type: "INTEGER", nullable: false),
                    RationSchemeId = table.Column<int>(type: "INTEGER", nullable: false),
                    DataSource = table.Column<string>(type: "TEXT", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Families", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Families_RationSchemes_RationSchemeId",
                        column: x => x.RationSchemeId,
                        principalTable: "RationSchemes",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Families_RationShops_RationShopId",
                        column: x => x.RationShopId,
                        principalTable: "RationShops",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "SchemeEntitlementItems",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    RationSchemeId = table.Column<int>(type: "INTEGER", nullable: false),
                    RationType = table.Column<int>(type: "INTEGER", nullable: false),
                    QuotaPerEligibleMemberPerMonth = table.Column<decimal>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_SchemeEntitlementItems", x => x.Id);
                    table.ForeignKey(
                        name: "FK_SchemeEntitlementItems_RationSchemes_RationSchemeId",
                        column: x => x.RationSchemeId,
                        principalTable: "RationSchemes",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Beneficiaries",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    BeneficiaryCode = table.Column<string>(type: "TEXT", nullable: false),
                    Address = table.Column<string>(type: "TEXT", nullable: false),
                    UserId = table.Column<int>(type: "INTEGER", nullable: false),
                    FamilyId = table.Column<int>(type: "INTEGER", nullable: false),
                    IsActive = table.Column<bool>(type: "INTEGER", nullable: false),
                    IsBlocked = table.Column<bool>(type: "INTEGER", nullable: false),
                    DataSource = table.Column<string>(type: "TEXT", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Beneficiaries", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Beneficiaries_Families_FamilyId",
                        column: x => x.FamilyId,
                        principalTable: "Families",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Beneficiaries_Users_UserId",
                        column: x => x.UserId,
                        principalTable: "Users",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "FamilyMembers",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    FamilyId = table.Column<int>(type: "INTEGER", nullable: false),
                    FullName = table.Column<string>(type: "TEXT", nullable: false),
                    Age = table.Column<int>(type: "INTEGER", nullable: false),
                    Relationship = table.Column<int>(type: "INTEGER", nullable: false),
                    Eligibility = table.Column<int>(type: "INTEGER", nullable: false),
                    DataSource = table.Column<string>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_FamilyMembers", x => x.Id);
                    table.ForeignKey(
                        name: "FK_FamilyMembers_Families_FamilyId",
                        column: x => x.FamilyId,
                        principalTable: "Families",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "AadhaarVerifications",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    BeneficiaryId = table.Column<int>(type: "INTEGER", nullable: false),
                    AadhaarReferenceId = table.Column<string>(type: "TEXT", nullable: false),
                    AadhaarMasked = table.Column<string>(type: "TEXT", nullable: false),
                    Status = table.Column<int>(type: "INTEGER", nullable: false),
                    VerificationDate = table.Column<DateTime>(type: "TEXT", nullable: true),
                    VerificationSource = table.Column<string>(type: "TEXT", nullable: false),
                    VerificationMode = table.Column<string>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AadhaarVerifications", x => x.Id);
                    table.ForeignKey(
                        name: "FK_AadhaarVerifications_Beneficiaries_BeneficiaryId",
                        column: x => x.BeneficiaryId,
                        principalTable: "Beneficiaries",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "MobileVerifications",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    BeneficiaryId = table.Column<int>(type: "INTEGER", nullable: false),
                    MobileMasked = table.Column<string>(type: "TEXT", nullable: false),
                    Status = table.Column<int>(type: "INTEGER", nullable: false),
                    VerifiedAt = table.Column<DateTime>(type: "TEXT", nullable: true),
                    VerificationSource = table.Column<string>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_MobileVerifications", x => x.Id);
                    table.ForeignKey(
                        name: "FK_MobileVerifications_Beneficiaries_BeneficiaryId",
                        column: x => x.BeneficiaryId,
                        principalTable: "Beneficiaries",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "OtpVerifications",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    BeneficiaryId = table.Column<int>(type: "INTEGER", nullable: false),
                    RequestedByUserId = table.Column<int>(type: "INTEGER", nullable: false),
                    OtpHash = table.Column<string>(type: "TEXT", nullable: false),
                    AttemptCount = table.Column<int>(type: "INTEGER", nullable: false),
                    MaxAttempts = table.Column<int>(type: "INTEGER", nullable: false),
                    Status = table.Column<int>(type: "INTEGER", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "TEXT", nullable: false),
                    ExpiresAt = table.Column<DateTime>(type: "TEXT", nullable: false),
                    VerifiedAt = table.Column<DateTime>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_OtpVerifications", x => x.Id);
                    table.ForeignKey(
                        name: "FK_OtpVerifications_Beneficiaries_BeneficiaryId",
                        column: x => x.BeneficiaryId,
                        principalTable: "Beneficiaries",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "PassbookVerifications",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    BeneficiaryId = table.Column<int>(type: "INTEGER", nullable: false),
                    PassbookNumber = table.Column<string>(type: "TEXT", nullable: false),
                    Status = table.Column<string>(type: "TEXT", nullable: false),
                    VerificationStatus = table.Column<int>(type: "INTEGER", nullable: false),
                    LastUpdated = table.Column<DateTime>(type: "TEXT", nullable: false),
                    VerificationSource = table.Column<string>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PassbookVerifications", x => x.Id);
                    table.ForeignKey(
                        name: "FK_PassbookVerifications_Beneficiaries_BeneficiaryId",
                        column: x => x.BeneficiaryId,
                        principalTable: "Beneficiaries",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "RationCollections",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    CollectionCode = table.Column<string>(type: "TEXT", nullable: false),
                    TokenId = table.Column<int>(type: "INTEGER", nullable: false),
                    BeneficiaryId = table.Column<int>(type: "INTEGER", nullable: false),
                    RationShopId = table.Column<int>(type: "INTEGER", nullable: false),
                    OperatorUserId = table.Column<int>(type: "INTEGER", nullable: false),
                    VerificationMethod = table.Column<string>(type: "TEXT", nullable: false),
                    CollectedAt = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_RationCollections", x => x.Id);
                    table.ForeignKey(
                        name: "FK_RationCollections_Beneficiaries_BeneficiaryId",
                        column: x => x.BeneficiaryId,
                        principalTable: "Beneficiaries",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_RationCollections_RationShops_RationShopId",
                        column: x => x.RationShopId,
                        principalTable: "RationShops",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_RationCollections_Tokens_TokenId",
                        column: x => x.TokenId,
                        principalTable: "Tokens",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "RationCollectionItems",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    RationCollectionId = table.Column<int>(type: "INTEGER", nullable: false),
                    RationType = table.Column<int>(type: "INTEGER", nullable: false),
                    Quantity = table.Column<decimal>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_RationCollectionItems", x => x.Id);
                    table.ForeignKey(
                        name: "FK_RationCollectionItems_RationCollections_RationCollectionId",
                        column: x => x.RationCollectionId,
                        principalTable: "RationCollections",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_AadhaarVerifications_BeneficiaryId",
                table: "AadhaarVerifications",
                column: "BeneficiaryId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Beneficiaries_BeneficiaryCode",
                table: "Beneficiaries",
                column: "BeneficiaryCode",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Beneficiaries_FamilyId",
                table: "Beneficiaries",
                column: "FamilyId");

            migrationBuilder.CreateIndex(
                name: "IX_Beneficiaries_UserId",
                table: "Beneficiaries",
                column: "UserId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Families_FamilyCode",
                table: "Families",
                column: "FamilyCode",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Families_RationSchemeId",
                table: "Families",
                column: "RationSchemeId");

            migrationBuilder.CreateIndex(
                name: "IX_Families_RationShopId",
                table: "Families",
                column: "RationShopId");

            migrationBuilder.CreateIndex(
                name: "IX_FamilyMembers_FamilyId",
                table: "FamilyMembers",
                column: "FamilyId");

            migrationBuilder.CreateIndex(
                name: "IX_MobileVerifications_BeneficiaryId",
                table: "MobileVerifications",
                column: "BeneficiaryId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_OtpVerifications_BeneficiaryId",
                table: "OtpVerifications",
                column: "BeneficiaryId");

            migrationBuilder.CreateIndex(
                name: "IX_PassbookVerifications_BeneficiaryId",
                table: "PassbookVerifications",
                column: "BeneficiaryId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_RationCollectionItems_RationCollectionId",
                table: "RationCollectionItems",
                column: "RationCollectionId");

            migrationBuilder.CreateIndex(
                name: "IX_RationCollections_BeneficiaryId",
                table: "RationCollections",
                column: "BeneficiaryId");

            migrationBuilder.CreateIndex(
                name: "IX_RationCollections_CollectionCode",
                table: "RationCollections",
                column: "CollectionCode",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_RationCollections_RationShopId",
                table: "RationCollections",
                column: "RationShopId");

            migrationBuilder.CreateIndex(
                name: "IX_RationCollections_TokenId",
                table: "RationCollections",
                column: "TokenId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_RationSchemes_SchemeCode",
                table: "RationSchemes",
                column: "SchemeCode",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_SchemeEntitlementItems_RationSchemeId_RationType",
                table: "SchemeEntitlementItems",
                columns: new[] { "RationSchemeId", "RationType" },
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "AadhaarVerifications");

            migrationBuilder.DropTable(
                name: "FamilyMembers");

            migrationBuilder.DropTable(
                name: "MobileVerifications");

            migrationBuilder.DropTable(
                name: "OtpVerifications");

            migrationBuilder.DropTable(
                name: "PassbookVerifications");

            migrationBuilder.DropTable(
                name: "RationCollectionItems");

            migrationBuilder.DropTable(
                name: "SchemeEntitlementItems");

            migrationBuilder.DropTable(
                name: "VerificationAuditLogs");

            migrationBuilder.DropTable(
                name: "RationCollections");

            migrationBuilder.DropTable(
                name: "Beneficiaries");

            migrationBuilder.DropTable(
                name: "Families");

            migrationBuilder.DropTable(
                name: "RationSchemes");

            migrationBuilder.DropColumn(
                name: "Taluka",
                table: "RationShops");

            migrationBuilder.DropColumn(
                name: "Village",
                table: "RationShops");
        }
    }
}
