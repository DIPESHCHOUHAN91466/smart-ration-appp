using SmartRation.Api.Models;
using SmartRation.Api.Services.AI;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

public class AIServicesTests
{
    [Fact]
    public async Task InventoryRiskService_BelowHalfMinimum_ReportsCritical()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            // MinimumStockLevel is 10 in ScenarioBuilder; riceInventory below 5 (half of 10) must be CRITICAL.
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 4);
            var service = new InventoryRiskService(db);

            var risks = await service.GetRisksAsync(scenario.Shop.Id);

            var riceRisk = Assert.Single(risks, r => r.RationType == "Rice");
            Assert.Equal("CRITICAL", riceRisk.CurrentStatus);
        }
    }

    [Fact]
    public async Task InventoryRiskService_WellAboveMinimum_ReportsNormal()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 500);
            var service = new InventoryRiskService(db);

            var risks = await service.GetRisksAsync(scenario.Shop.Id);

            var riceRisk = Assert.Single(risks, r => r.RationType == "Rice");
            Assert.Equal("NORMAL", riceRisk.CurrentStatus);
        }
    }

    [Fact]
    public async Task BeneficiaryInsightService_NoRecentActivity_ReportsLowRisk()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var service = new BeneficiaryInsightService(db);

            var insight = await service.GetBeneficiaryInsightAsync(scenario.Beneficiary.Id);

            Assert.Equal("Low", insight.RiskLevel);
        }
    }

    [Fact]
    public async Task BeneficiaryInsightService_RepeatedBlockedVerifications_ReportsElevatedRisk()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            for (var i = 0; i < 3; i++)
            {
                db.VerificationAuditLogs.Add(new VerificationAuditLog
                {
                    BeneficiaryId = scenario.Beneficiary.Id,
                    Action = VerificationAction.BeneficiaryVerified,
                    VerificationMethod = "QR",
                    Status = "BLOCKED",
                    Reason = "Test block",
                    Timestamp = DateTime.UtcNow
                });
            }
            db.SaveChanges();

            var service = new BeneficiaryInsightService(db);
            var insight = await service.GetBeneficiaryInsightAsync(scenario.Beneficiary.Id);

            Assert.Equal("High", insight.RiskLevel);
            Assert.Contains(insight.Reasons, r => r.Contains("blocked"));
        }
    }

    // Duplicate-collection-attempt is the shop-scoped anomaly check (it
    // passes shopId to UpsertAlertAsync), so it's the one that should also
    // notify that shop's owner — RepeatedQrScan is beneficiary-scoped only.
    [Fact]
    public async Task AnomalyDetectionService_DuplicateCollectionAttempts_CreatesOpenAlertAndShopNotification()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);

            var owner = new User { FullName = "Shop Owner", Email = $"owner{Guid.NewGuid():N}@example.com", MobileNumber = "9000000000", PasswordHash = "x", Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id, IsActive = true };
            db.Users.Add(owner);
            db.SaveChanges();

            for (var i = 0; i < 2; i++)
            {
                db.VerificationAuditLogs.Add(new VerificationAuditLog
                {
                    BeneficiaryId = scenario.Beneficiary.Id,
                    ShopId = scenario.Shop.Id,
                    TokenNumber = scenario.Token.TokenNumber,
                    Action = VerificationAction.CollectionRejected,
                    VerificationMethod = "QR",
                    Status = "BLOCKED",
                    Timestamp = DateTime.UtcNow
                });
            }
            db.SaveChanges();

            var service = new AnomalyDetectionService(db);
            var alerts = await service.ScanAndDetectAsync();

            Assert.Contains(alerts, a => a.AlertType == "DuplicateCollectionAttempt" && a.Status == AIAlertStatus.Open);

            var notification = Assert.Single(db.Notifications, n => n.UserId == owner.Id);
            Assert.Equal(NotificationType.AIAlert, notification.Type);
        }
    }

    [Fact]
    public async Task AnomalyDetectionService_RepeatedQrScans_CreatesOpenAlertWithoutShopNotification()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);

            for (var i = 0; i < 4; i++)
            {
                db.VerificationAuditLogs.Add(new VerificationAuditLog
                {
                    BeneficiaryId = scenario.Beneficiary.Id,
                    ShopId = scenario.Shop.Id,
                    Action = VerificationAction.QrScanned,
                    VerificationMethod = "QR",
                    Status = "SUCCESS",
                    Timestamp = DateTime.UtcNow
                });
            }
            db.SaveChanges();

            var service = new AnomalyDetectionService(db);
            var alerts = await service.ScanAndDetectAsync();

            Assert.Contains(alerts, a => a.AlertType == "RepeatedQrScan" && a.Status == AIAlertStatus.Open);
            // This check is beneficiary-scoped, not shop-scoped, so it does not notify a shop owner.
            Assert.Empty(db.Notifications);
        }
    }

    [Fact]
    public async Task AnomalyDetectionService_SecondScanWithinWindow_DoesNotDuplicateOpenAlert()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            for (var i = 0; i < 4; i++)
            {
                db.VerificationAuditLogs.Add(new VerificationAuditLog
                {
                    BeneficiaryId = scenario.Beneficiary.Id,
                    ShopId = scenario.Shop.Id,
                    Action = VerificationAction.QrScanned,
                    VerificationMethod = "QR",
                    Status = "SUCCESS",
                    Timestamp = DateTime.UtcNow
                });
            }
            db.SaveChanges();

            var service = new AnomalyDetectionService(db);
            await service.ScanAndDetectAsync();
            await service.ScanAndDetectAsync();

            var openAlerts = db.AIAlerts.Where(a => a.AlertType == "RepeatedQrScan" && a.BeneficiaryId == scenario.Beneficiary.Id && a.Status == AIAlertStatus.Open);
            Assert.Single(openAlerts);
        }
    }
}
