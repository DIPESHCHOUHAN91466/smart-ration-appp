using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.AI;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

// The rules BeneficiariesController used to implement inline, now in BeneficiaryProfileService:
// who may see a beneficiary, what the profile contains, and the missing-mobile-record repair.
public class BeneficiaryProfileServiceTests
{
    private sealed class StubInsights : IBeneficiaryInsightService
    {
        public Task<BeneficiaryRiskInsightDto> GetBeneficiaryInsightAsync(int beneficiaryId) =>
            Task.FromResult(new BeneficiaryRiskInsightDto { RiskLevel = "Low" });
    }

    private static BeneficiaryProfileService Build(SmartRationDbContext db, FakeCurrentUserService user)
    {
        var graph = new TestServiceGraph(db, user);
        return new BeneficiaryProfileService(db, graph.Aadhaar, graph.Passbook, graph.Entitlement, new StubInsights(), user);
    }

    private static User AddOtherRuralUser(SmartRationDbContext db)
    {
        var other = new User { FullName = "Other Citizen", Email = $"other{Guid.NewGuid():N}@example.com", MobileNumber = ScenarioBuilder.NextSyntheticMobile(), PasswordHash = "x", Role = UserRole.RuralUser, IsActive = true };
        db.Users.Add(other);
        db.SaveChanges();
        return other;
    }

    [Fact]
    public async Task RuralUser_CanReadOwnProfile()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var service = Build(db, new FakeCurrentUserService { UserId = scenario.BeneficiaryUser.Id, Role = UserRole.RuralUser });

            Assert.Equal(scenario.Beneficiary.Id, await service.GetMyBeneficiaryIdAsync());
            var profile = await service.GetVerificationAsync(scenario.Beneficiary.Id);
            Assert.Equal(scenario.Beneficiary.BeneficiaryCode, profile.Beneficiary.BeneficiaryCode);
            Assert.Equal(scenario.Family.FamilyCode, (await service.GetFamilyAsync(scenario.Beneficiary.Id)).FamilyCode);
        }
    }

    [Fact]
    public async Task RuralUser_IsForbiddenFromAnotherCitizensProfile()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var other = AddOtherRuralUser(db);
            var service = Build(db, new FakeCurrentUserService { UserId = other.Id, Role = UserRole.RuralUser });

            await Assert.ThrowsAsync<ForbiddenException>(() => service.GetVerificationAsync(scenario.Beneficiary.Id));
            await Assert.ThrowsAsync<ForbiddenException>(() => service.GetFullProfileAsync(scenario.Beneficiary.Id));
            await Assert.ThrowsAsync<ForbiddenException>(() => service.GetCollectionHistoryAsync(scenario.Beneficiary.Id));
            await Assert.ThrowsAsync<NotFoundException>(() => service.GetMyBeneficiaryIdAsync()); // has no profile of their own
        }
    }

    [Theory]
    [InlineData(UserRole.ShopOwner)]
    [InlineData(UserRole.GovernmentOfficial)]
    [InlineData(UserRole.Admin)]
    public async Task StaffRoles_CanReadAnyProfile(UserRole role)
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var service = Build(db, new FakeCurrentUserService { UserId = 999, Role = role });

            var entitlement = await service.GetEntitlementAsync(scenario.Beneficiary.Id);
            Assert.Contains(entitlement.Items, i => i.RationType == "Rice");
        }
    }

    [Fact]
    public async Task UnknownBeneficiary_IsNotFound()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            ScenarioBuilder.SeedBasicScenario(db);
            var service = Build(db, new FakeCurrentUserService { UserId = 1, Role = UserRole.Admin });
            await Assert.ThrowsAsync<NotFoundException>(() => service.GetFamilyAsync(424242));
        }
    }

    [Fact]
    public async Task FullProfile_ShowsUpcomingToken_MaskedMobile_AndCollections()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            db.RationCollections.Add(new RationCollection
            {
                CollectionCode = "COL-TEST-000001", TokenId = scenario.Token.Id, BeneficiaryId = scenario.Beneficiary.Id,
                RationShopId = scenario.Shop.Id, OperatorUserId = 1, VerificationMethod = "QR", CollectedAt = DateTime.UtcNow.AddDays(-3),
                Items = [new RationCollectionItem { RationType = RationType.Rice, Quantity = 5 }]
            });
            db.SaveChanges();
            var service = Build(db, new FakeCurrentUserService { UserId = scenario.BeneficiaryUser.Id, Role = UserRole.RuralUser });

            var full = await service.GetFullProfileAsync(scenario.Beneficiary.Id);

            Assert.Equal(scenario.Token.TokenNumber, full.CurrentQr?.TokenNumber);
            Assert.StartsWith("******", full.Profile.MobileMasked);
            Assert.DoesNotContain(scenario.BeneficiaryUser.MobileNumber, full.Profile.MobileMasked);
            var collection = Assert.Single(full.CollectionHistory);
            Assert.Equal("COL-TEST-000001", collection.CollectionCode);
            Assert.Equal(5, Assert.Single(collection.Items).Quantity);
            Assert.Equal(collection.CollectionCode, Assert.Single(await service.GetCollectionHistoryAsync(scenario.Beneficiary.Id)).CollectionCode);
            Assert.Equal("Low", full.AIInsight.RiskLevel);
        }
    }

    [Fact]
    public async Task MissingMobileVerification_IsCreatedOnce_AsNotVerifiedSynthetic()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            db.MobileVerifications.RemoveRange(db.MobileVerifications);
            db.SaveChanges();
            db.ChangeTracker.Clear();
            var service = Build(db, new FakeCurrentUserService { UserId = scenario.BeneficiaryUser.Id, Role = UserRole.RuralUser });

            var profile = await service.GetVerificationAsync(scenario.Beneficiary.Id);
            await service.GetVerificationAsync(scenario.Beneficiary.Id);

            Assert.Equal("NotVerified", profile.MobileVerification.Status);
            var stored = await db.MobileVerifications.SingleAsync();
            Assert.Equal("SYNTHETIC_DEMO", stored.VerificationSource);
        }
    }
}
