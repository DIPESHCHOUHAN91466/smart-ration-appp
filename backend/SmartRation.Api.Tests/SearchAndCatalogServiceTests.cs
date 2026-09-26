using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.AI;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

// The rules that moved out of SearchController, RationController, RationCollectionController,
// SyntheticDataController and AIController (Phase C, part 2 of the third audit).
public class SearchAndCatalogServiceTests
{
    // A second shop with its own citizen, family, beneficiary and token, so scoping can be checked.
    private record OtherShop(RationShop Shop, User Citizen, Beneficiary Beneficiary, Token Token);

    private static OtherShop SeedOtherShop(SmartRationDbContext db, BasicScenario main)
    {
        var shop = new RationShop { ShopName = "Other Shop", ShopCode = "SHOP-TEST-002", Address = "Test", District = "Elsewhere", State = "Test", IsActive = true };
        db.RationShops.Add(shop);
        var citizen = new User { FullName = "Test Neighbour", Email = $"n{Guid.NewGuid():N}@example.com", MobileNumber = ScenarioBuilder.NextSyntheticMobile(), PasswordHash = "x", Role = UserRole.RuralUser, IsActive = true };
        db.Users.Add(citizen);
        db.SaveChanges();
        var family = new Family { FamilyCode = "FAM-TEST-0002", RationShopId = shop.Id, RationSchemeId = main.Scheme.Id, DataSource = "SYNTHETIC_DEMO" };
        db.Families.Add(family);
        db.SaveChanges();
        var beneficiary = new Beneficiary { BeneficiaryCode = "BEN-TEST-0002", Address = "Test", District = "Elsewhere", UserId = citizen.Id, FamilyId = family.Id, IsActive = true, DataSource = "SYNTHETIC_DEMO" };
        db.Beneficiaries.Add(beneficiary);
        var slot = new TimeSlot { RationShopId = shop.Id, SlotDate = DateTime.UtcNow.Date, StartTime = TimeSpan.FromHours(10), EndTime = TimeSpan.FromHours(10).Add(TimeSpan.FromMinutes(5)), Capacity = 5, BookedCount = 1 };
        db.TimeSlots.Add(slot);
        db.SaveChanges();
        var token = new Token { TokenNumber = "SR-TEST-000002", UserId = citizen.Id, RationShopId = shop.Id, TimeSlotId = slot.Id, Status = TokenStatus.Confirmed, CreatedAt = DateTime.UtcNow };
        db.Tokens.Add(token);
        db.SaveChanges();
        return new OtherShop(shop, citizen, beneficiary, token);
    }

    private static List<string> Search(SmartRationDbContext db, FakeCurrentUserService user, string q) =>
        new SearchService(db, user).SearchAsync(q).Result.Select(r => $"{r.Type}:{r.Subtitle ?? r.Title}").ToList();

    // ---- SearchService: role scoping (security-critical) ----

    [Fact]
    public void Search_RuralUser_SeesOnlyOwnBeneficiaryAndTokens()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var main = ScenarioBuilder.SeedBasicScenario(db);
            SeedOtherShop(db, main);
            var me = new FakeCurrentUserService { UserId = main.BeneficiaryUser.Id, Role = UserRole.RuralUser };

            Assert.Equal(new[] { "Beneficiary:BEN-TEST-0001" }, Search(db, me, "BEN-TEST"));
            Assert.Equal(new[] { "Token:Test Shop" }, Search(db, me, "SR-TEST"));
            Assert.DoesNotContain(Search(db, me, "shop"), r => r.StartsWith("Shop:"));
        }
    }

    [Fact]
    public void Search_ShopOwner_SeesOnlyOwnShop()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var main = ScenarioBuilder.SeedBasicScenario(db);
            var other = SeedOtherShop(db, main);
            var owner = new FakeCurrentUserService { UserId = 900, Role = UserRole.ShopOwner, RationShopId = other.Shop.Id };

            Assert.Equal(new[] { "Beneficiary:BEN-TEST-0002" }, Search(db, owner, "BEN-TEST"));
            Assert.Equal(new[] { "Token:Other Shop" }, Search(db, owner, "SR-TEST"));

            // An owner account not linked to any shop sees no beneficiaries or tokens at all.
            Assert.Empty(Search(db, new FakeCurrentUserService { UserId = 901, Role = UserRole.ShopOwner, RationShopId = null }, "TEST"));
        }
    }

    [Fact]
    public void Search_Official_SeesEverythingIncludingShops()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var main = ScenarioBuilder.SeedBasicScenario(db);
            SeedOtherShop(db, main);
            var official = new FakeCurrentUserService { UserId = 902, Role = UserRole.GovernmentOfficial };

            Assert.Equal(2, Search(db, official, "BEN-TEST").Count);
            Assert.Equal(new[] { "Shop:SHOP-TEST-001", "Shop:SHOP-TEST-002" }, Search(db, official, "SHOP-TEST"));
        }
    }

    [Fact]
    public void Search_ShortOrEmptyQuery_ReturnsNothing()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            ScenarioBuilder.SeedBasicScenario(db);
            var admin = new FakeCurrentUserService { UserId = 903, Role = UserRole.Admin };
            Assert.Empty(Search(db, admin, "B"));
            Assert.Empty(Search(db, admin, "   "));
        }
    }

    // ---- RationCatalogService ----

    [Fact]
    public async Task Catalog_AddsShopStock_AndOnlyTheCitizensOwnEntitlement()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var main = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 80);
            var entitlement = new TestServiceGraph(db, new FakeCurrentUserService()).Entitlement;

            var citizen = new RationCatalogService(db, entitlement, new FakeCurrentUserService { UserId = main.BeneficiaryUser.Id, Role = UserRole.RuralUser });
            var rice = (await citizen.GetItemsAsync(main.Shop.Id)).Single(i => i.RationType == "Rice");
            Assert.Equal(80, rice.AvailableQuantity);
            Assert.NotNull(rice.EligibleQuantity);

            var official = new RationCatalogService(db, entitlement, new FakeCurrentUserService { UserId = 904, Role = UserRole.GovernmentOfficial });
            var items = await official.GetItemsAsync(shopId: null);
            Assert.Equal(2, items.Count);
            Assert.All(items, i => Assert.Null(i.EligibleQuantity));
        }
    }

    // ---- Collection history and AI insight: the shared BeneficiaryAccess rule ----

    private sealed class StubInsights : IBeneficiaryInsightService
    {
        public Task<BeneficiaryRiskInsightDto> GetBeneficiaryInsightAsync(int beneficiaryId) =>
            Task.FromResult(new BeneficiaryRiskInsightDto { RiskLevel = "Low" });
    }

    private static BeneficiaryProfileService Profiles(SmartRationDbContext db, FakeCurrentUserService user)
    {
        var graph = new TestServiceGraph(db, user);
        return new BeneficiaryProfileService(db, graph.Aadhaar, graph.Passbook, graph.Entitlement, new StubInsights(), user);
    }

    [Fact]
    public async Task HistoryAndInsight_CitizenLimitedToOwn_StaffSeeAny()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var main = ScenarioBuilder.SeedBasicScenario(db);
            var other = SeedOtherShop(db, main);
            var me = Profiles(db, new FakeCurrentUserService { UserId = main.BeneficiaryUser.Id, Role = UserRole.RuralUser });

            Assert.Empty(await me.GetCollectionHistoryAsync(main.Beneficiary.Id));
            await me.EnsureCanSeeAsync(main.Beneficiary.Id);
            await Assert.ThrowsAsync<ForbiddenException>(() => me.GetCollectionHistoryAsync(other.Beneficiary.Id));
            await Assert.ThrowsAsync<ForbiddenException>(() => me.EnsureCanSeeAsync(other.Beneficiary.Id));

            var official = Profiles(db, new FakeCurrentUserService { UserId = 905, Role = UserRole.GovernmentOfficial });
            await official.EnsureCanSeeAsync(other.Beneficiary.Id);
            await Assert.ThrowsAsync<NotFoundException>(() => official.EnsureCanSeeAsync(424242));
        }
    }

    // ---- AdminDatabaseBrowserService with the synthetic-data screen's filters ----

    [Fact]
    public async Task SyntheticFilters_DistrictStatusAndMobileSearch()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var main = ScenarioBuilder.SeedBasicScenario(db);
            var other = SeedOtherShop(db, main);
            var browser = new AdminDatabaseBrowserService(db);

            Assert.Equal(1, (await browser.GetBeneficiariesAsync(null, 1, 20, new BeneficiaryFilter(District: "Elsewhere"))).TotalCount);
            Assert.Equal(1, (await browser.GetBeneficiariesAsync(null, 1, 20, new BeneficiaryFilter(AadhaarStatus: "verified"))).TotalCount);
            Assert.Equal(2, (await browser.GetBeneficiariesAsync(null, 1, 20, new BeneficiaryFilter(AadhaarStatus: "not-a-status"))).TotalCount); // ignored

            // Mobile search only when asked for (the database viewer does not search mobiles).
            Assert.Equal(1, (await browser.GetBeneficiariesAsync(other.Citizen.MobileNumber, 1, 20, new BeneficiaryFilter(SearchMobile: true))).TotalCount);
            Assert.Equal(0, (await browser.GetBeneficiariesAsync(other.Citizen.MobileNumber, 1, 20)).TotalCount);
        }
    }
}
