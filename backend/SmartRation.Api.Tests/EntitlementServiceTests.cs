using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

public class EntitlementServiceTests
{
    // Scenario 16: Entitlement calculation.
    [Fact]
    public async Task GetEntitlementAsync_WithNoCollections_MonthlyEqualsRemaining()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceQuotaPerMember: 5);
            var service = new EntitlementService(db);

            var result = await service.GetEntitlementAsync(scenario.Family.Id);

            var rice = Assert.Single(result.Items, i => i.RationType == "Rice");
            Assert.Equal(1, result.EligibleMemberCount);
            Assert.Equal(5, rice.MonthlyEntitlement);
            Assert.Equal(0, rice.AlreadyCollected);
            Assert.Equal(5, rice.Remaining);
            Assert.Equal(5, rice.TodayAllocation); // capped at StandardQuotaPerBooking = 5
        }
    }

    [Fact]
    public async Task GetEntitlementAsync_AfterPartialCollectionThisMonth_ReducesRemaining()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceQuotaPerMember: 20);

            var collection = new RationCollection
            {
                CollectionCode = "COL-TEST-000001",
                TokenId = scenario.Token.Id,
                BeneficiaryId = scenario.Beneficiary.Id,
                RationShopId = scenario.Shop.Id,
                OperatorUserId = 1,
                VerificationMethod = "QR",
                CollectedAt = DateTime.UtcNow,
                Items = [new RationCollectionItem { RationType = RationType.Rice, Quantity = 12 }]
            };
            db.RationCollections.Add(collection);
            await db.SaveChangesAsync();

            var service = new EntitlementService(db);
            var result = await service.GetEntitlementAsync(scenario.Family.Id);

            var rice = Assert.Single(result.Items, i => i.RationType == "Rice");
            Assert.Equal(20, rice.MonthlyEntitlement);
            Assert.Equal(12, rice.AlreadyCollected);
            Assert.Equal(8, rice.Remaining);
            Assert.Equal(5, rice.TodayAllocation); // min(remaining=8, standardQuota=5)
        }
    }

    [Fact]
    public async Task GetEntitlementAsync_WhenFullyCollected_TodayAllocationIsZero()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceQuotaPerMember: 5);

            db.RationCollections.Add(new RationCollection
            {
                CollectionCode = "COL-TEST-000002",
                TokenId = scenario.Token.Id,
                BeneficiaryId = scenario.Beneficiary.Id,
                RationShopId = scenario.Shop.Id,
                OperatorUserId = 1,
                VerificationMethod = "QR",
                CollectedAt = DateTime.UtcNow,
                Items = [new RationCollectionItem { RationType = RationType.Rice, Quantity = 5 }]
            });
            await db.SaveChangesAsync();

            var service = new EntitlementService(db);
            var result = await service.GetEntitlementAsync(scenario.Family.Id);

            var rice = Assert.Single(result.Items, i => i.RationType == "Rice");
            Assert.Equal(0, rice.Remaining);
            Assert.Equal(0, rice.TodayAllocation);
        }
    }

    [Fact]
    public async Task GetEntitlementAsync_CollectionFromPreviousMonth_DoesNotCountTowardsThisMonth()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceQuotaPerMember: 5);

            db.RationCollections.Add(new RationCollection
            {
                CollectionCode = "COL-TEST-000003",
                TokenId = scenario.Token.Id,
                BeneficiaryId = scenario.Beneficiary.Id,
                RationShopId = scenario.Shop.Id,
                OperatorUserId = 1,
                VerificationMethod = "QR",
                CollectedAt = DateTime.UtcNow.AddMonths(-2),
                Items = [new RationCollectionItem { RationType = RationType.Rice, Quantity = 5 }]
            });
            await db.SaveChangesAsync();

            var service = new EntitlementService(db);
            var result = await service.GetEntitlementAsync(scenario.Family.Id);

            var rice = Assert.Single(result.Items, i => i.RationType == "Rice");
            Assert.Equal(0, rice.AlreadyCollected);
            Assert.Equal(5, rice.Remaining);
        }
    }
}
