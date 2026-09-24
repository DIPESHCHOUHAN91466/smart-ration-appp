using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;
using SmartRation.Api.Services.AI;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

public class AiAlertServiceTests
{
    private class FakeAi(Func<PythonAiResult> respond) : IPythonAiClient
    {
        public int Calls { get; private set; }
        public bool IsConfigured => true;
        public Task<PythonAiResult> GetAsync(string path, IDictionary<string, string?> query, CancellationToken ct = default)
        {
            Calls++;
            return Task.FromResult(respond());
        }
        public Task<PythonAiResult> PostAsync(string path, object body, CancellationToken ct = default) => throw new NotSupportedException();
        public Task<bool> IsHealthyAsync(CancellationToken ct = default) => Task.FromResult(true);
    }

    private static PythonAiResult Candidates(string json) =>
        new(true, JsonDocument.Parse(json).RootElement.Clone(), null, null);

    private static string LowStock(int shopId, string severity = "HIGH", double score = 85) => JsonSerializer.Serialize(new
    {
        items = new[]
        {
            new
            {
                dedup_key = $"LOW_STOCK:{shopId}:Rice", alert_type = "LOW_STOCK", severity, shop_id = shopId, ration_type = 1,
                title = "Rice: critical", description = "Only ~2 days of stock left.", score, recommended_action = "Reorder.",
                metadata = new { stock = 4, avg_daily_consumption = 2 }
            }
        }
    });

    private static AiAlertService Build(Data.SmartRationDbContext db, IPythonAiClient ai, UserRole role, int? shopId = null)
    {
        var user = new FakeCurrentUserService { UserId = 1, Role = role, RationShopId = shopId };
        return new AiAlertService(db, ai, user, new TestServiceGraph(db, user).AuditLog, NullLogger<AiAlertService>.Instance);
    }

    [Fact]
    public async Task RepeatedSync_DoesNotDuplicate_AndKeepsReasonScoreAndMetadata()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var service = Build(db, new FakeAi(() => Candidates(LowStock(scenario.Shop.Id))), UserRole.GovernmentOfficial);

            var first = await service.SyncFromPythonAsync(force: true);
            var second = await service.SyncFromPythonAsync(force: true);
            var third = await service.SyncFromPythonAsync(force: true);

            Assert.Equal((1, 0), (first.Created, first.Updated));
            Assert.Equal((0, 1), (second.Created, second.Updated));
            Assert.Equal(0, third.Created);
            var alert = await db.AIAlerts.SingleAsync();
            Assert.Equal("PYTHON_AI", alert.Source);
            Assert.Equal(85, alert.Score);
            Assert.Equal(RationType.Rice, alert.RationType);
            Assert.Contains("stock", alert.MetadataJson);
            Assert.Equal("Only ~2 days of stock left.", alert.Description);
        }
    }

    [Fact]
    public async Task ResolvedAlert_IsRaisedAgainOnlyIfStillDetected()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var service = Build(db, new FakeAi(() => Candidates(LowStock(scenario.Shop.Id))), UserRole.GovernmentOfficial);

            await service.SyncFromPythonAsync(force: true);
            var id = (await db.AIAlerts.SingleAsync()).Id;
            await service.ResolveAsync(id, new ResolveAiAlertRequestDto { Status = "Resolved", Note = "Stock delivered" });
            await service.SyncFromPythonAsync(force: true);

            Assert.Equal(2, await db.AIAlerts.CountAsync());
            Assert.Equal(1, await db.AIAlerts.CountAsync(a => a.Status == AIAlertStatus.Open));
        }
    }

    [Fact]
    public async Task AutomaticSync_IsThrottled()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var ai = new FakeAi(() => Candidates(LowStock(scenario.Shop.Id)));
            var service = Build(db, ai, UserRole.GovernmentOfficial);

            await service.SyncFromPythonAsync(force: true);
            var again = await service.SyncFromPythonAsync(force: false);

            Assert.True(again.Skipped);
            Assert.Equal(1, ai.Calls);
        }
    }

    [Theory]
    [InlineData("""{"items":"not-a-list"}""")]
    [InlineData("""{"nothing":true}""")]
    public async Task MalformedResponse_CreatesNothing(string json)
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            ScenarioBuilder.SeedBasicScenario(db);
            var result = await Build(db, new FakeAi(() => Candidates(json)), UserRole.GovernmentOfficial).SyncFromPythonAsync(force: true);

            Assert.False(result.Available);
            Assert.Equal("AI_MALFORMED_RESPONSE", result.ErrorCode);
            Assert.Equal(0, await db.AIAlerts.CountAsync());
        }
    }

    [Fact]
    public async Task InvalidCandidates_AreRejectedIndividually()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var json = $$"""
                {"items":[
                  {"dedup_key":"X:1","alert_type":"LOW_STOCK","severity":"APOCALYPTIC","shop_id":{{scenario.Shop.Id}}},
                  {"alert_type":"LOW_STOCK","severity":"HIGH"},
                  {"dedup_key":"DEMAND_SPIKE:{{scenario.Shop.Id}}:Rice","alert_type":"DEMAND_SPIKE","severity":"MEDIUM","shop_id":{{scenario.Shop.Id}},"score":999}
                ]}
                """;
            var result = await Build(db, new FakeAi(() => Candidates(json)), UserRole.GovernmentOfficial).SyncFromPythonAsync(force: true);

            Assert.Equal((1, 2), (result.Created, result.Rejected));
            Assert.Equal(100, (await db.AIAlerts.SingleAsync()).Score); // clamped
        }
    }

    [Fact]
    public async Task AiUnavailable_ReportsItAndCreatesNothing()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            ScenarioBuilder.SeedBasicScenario(db);
            var ai = new FakeAi(() => new PythonAiResult(false, null, "AI_UNAVAILABLE", "down"));
            var result = await Build(db, ai, UserRole.GovernmentOfficial).SyncFromPythonAsync(force: true);

            Assert.False(result.Available);
            Assert.Equal("AI_UNAVAILABLE", result.ErrorCode);
            Assert.Equal(0, await db.AIAlerts.CountAsync());
        }
    }

    [Fact]
    public async Task ShopOwner_SeesOnlyOwnShop_AndCannotResolve()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var otherShop = scenario.Shop.Id + 50;
            var json = $$"""{"items":[{"dedup_key":"A","alert_type":"LOW_STOCK","severity":"HIGH","shop_id":{{scenario.Shop.Id}}},{"dedup_key":"B","alert_type":"LOW_STOCK","severity":"HIGH","shop_id":{{otherShop}}},{"dedup_key":"C","alert_type":"FORECAST_RISK","severity":"LOW"}]}""";
            await Build(db, new FakeAi(() => Candidates(json)), UserRole.GovernmentOfficial).SyncFromPythonAsync(force: true);

            var owner = Build(db, new FakeAi(() => Candidates(json)), UserRole.ShopOwner, scenario.Shop.Id);
            var visible = await owner.ListAsync(new AiAlertQuery("all", otherShop, null, 50)); // asks for another shop

            Assert.Empty(visible);
            Assert.Single(await owner.ListAsync(new AiAlertQuery("all", null, null, 50)));
            var foreign = await db.AIAlerts.SingleAsync(a => a.DedupKey == "B");
            await Assert.ThrowsAsync<NotFoundException>(() => owner.GetAsync(foreign.Id));
            await Assert.ThrowsAsync<ForbiddenException>(() => owner.ResolveAsync(foreign.Id, new ResolveAiAlertRequestDto { Status = "Resolved" }));
        }
    }
}
