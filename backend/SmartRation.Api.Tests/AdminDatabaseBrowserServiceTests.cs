using SmartRation.Api.Services;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

// The read-only paged table views behind AdminDatabaseController.
public class AdminDatabaseBrowserServiceTests
{
    [Fact]
    public async Task Beneficiaries_ArePagedAndSearchable_ByCodeOrName()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var browser = new AdminDatabaseBrowserService(db);

            var all = await browser.GetBeneficiariesAsync(null, 1, 25);
            Assert.Equal(1, all.TotalCount);
            Assert.Equal(scenario.Beneficiary.BeneficiaryCode, Assert.Single(all.Items).BeneficiaryCode);

            Assert.Equal(1, (await browser.GetBeneficiariesAsync("ben-test", 1, 25)).TotalCount);      // code, case-insensitive
            Assert.Equal(1, (await browser.GetBeneficiariesAsync("test beneficiary", 1, 25)).TotalCount); // name
            Assert.Equal(0, (await browser.GetBeneficiariesAsync("' OR '1'='1", 1, 25)).TotalCount);   // just text

            var secondPage = await browser.GetBeneficiariesAsync(null, 2, 25);
            Assert.Equal(1, secondPage.TotalCount);
            Assert.Empty(secondPage.Items);
        }
    }

    [Fact]
    public async Task Tokens_Inventory_And_AuditLogs_AreListed_ReadOnly()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var browser = new AdminDatabaseBrowserService(db);
            var before = db.ChangeTracker.Entries().Count();

            var token = Assert.Single((await browser.GetTokensAsync(null, 1, 25)).Items);
            Assert.Equal(scenario.Token.TokenNumber, token.TokenNumber);
            Assert.Equal(scenario.Beneficiary.BeneficiaryCode, token.BeneficiaryCode);
            Assert.Single((await browser.GetInventoryAsync(1, 25)).Items);
            Assert.Empty((await browser.GetAuditLogsAsync(1, 25)).Items);
            Assert.Empty((await browser.GetCollectionsAsync(null, 1, 25)).Items);

            Assert.False(db.ChangeTracker.HasChanges());
            Assert.True(db.ChangeTracker.Entries().Count() >= before);
        }
    }
}
