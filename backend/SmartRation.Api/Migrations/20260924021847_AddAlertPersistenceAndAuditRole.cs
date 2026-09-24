using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SmartRation.Api.Migrations
{
    /// <inheritdoc />
    public partial class AddAlertPersistenceAndAuditRole : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "Result",
                table: "AuditLogs",
                type: "TEXT",
                maxLength: 16,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "Role",
                table: "AuditLogs",
                type: "TEXT",
                maxLength: 32,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "DedupKey",
                table: "AIAlerts",
                type: "TEXT",
                maxLength: 128,
                nullable: true);

            migrationBuilder.AddColumn<DateTime>(
                name: "DetectedAt",
                table: "AIAlerts",
                type: "TEXT",
                nullable: true);

            migrationBuilder.AddColumn<DateTime>(
                name: "LastSeenAt",
                table: "AIAlerts",
                type: "TEXT",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "MetadataJson",
                table: "AIAlerts",
                type: "TEXT",
                nullable: true);

            migrationBuilder.AddColumn<int>(
                name: "RationType",
                table: "AIAlerts",
                type: "INTEGER",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "RecommendedAction",
                table: "AIAlerts",
                type: "TEXT",
                maxLength: 500,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "ResolutionNote",
                table: "AIAlerts",
                type: "TEXT",
                maxLength: 500,
                nullable: true);

            migrationBuilder.AddColumn<int>(
                name: "ResolvedByUserId",
                table: "AIAlerts",
                type: "INTEGER",
                nullable: true);

            migrationBuilder.AddColumn<double>(
                name: "Score",
                table: "AIAlerts",
                type: "REAL",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "Source",
                table: "AIAlerts",
                type: "TEXT",
                maxLength: 32,
                nullable: false,
                defaultValue: "RULES");

            migrationBuilder.AddColumn<string>(
                name: "Title",
                table: "AIAlerts",
                type: "TEXT",
                maxLength: 200,
                nullable: true);

            migrationBuilder.CreateIndex(
                name: "IX_AIAlerts_DedupKey_Status",
                table: "AIAlerts",
                columns: new[] { "DedupKey", "Status" });

            migrationBuilder.CreateIndex(
                name: "IX_AIAlerts_ShopId_Status",
                table: "AIAlerts",
                columns: new[] { "ShopId", "Status" });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_AIAlerts_DedupKey_Status",
                table: "AIAlerts");

            migrationBuilder.DropIndex(
                name: "IX_AIAlerts_ShopId_Status",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "Result",
                table: "AuditLogs");

            migrationBuilder.DropColumn(
                name: "Role",
                table: "AuditLogs");

            migrationBuilder.DropColumn(
                name: "DedupKey",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "DetectedAt",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "LastSeenAt",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "MetadataJson",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "RationType",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "RecommendedAction",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "ResolutionNote",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "ResolvedByUserId",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "Score",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "Source",
                table: "AIAlerts");

            migrationBuilder.DropColumn(
                name: "Title",
                table: "AIAlerts");
        }
    }
}
