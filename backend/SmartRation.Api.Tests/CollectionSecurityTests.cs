using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

// One security model for every collection path: the QR-verified confirm and
// the shop queue's quick complete must enforce the same eligibility,
// entitlement, token and all-or-nothing stock rules.
public class CollectionSecurityTests
{
    private static (TestServiceGraph Graph, ShopService Shop) Build(Data.SmartRationDbContext db, int shopId)
    {
        var graph = new TestServiceGraph(db, new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = shopId });
        return (graph, new ShopService(db, graph.CurrentUser, graph.BuildCollectionService()));
    }

    private static async Task SetRiceRequest(Data.SmartRationDbContext db, int tokenId, decimal quantity)
    {
        var item = await db.TokenItems.SingleAsync(i => i.TokenId == tokenId && i.RationType == RationType.Rice);
        item.Quantity = quantity;
        await db.SaveChangesAsync();
    }

    private static Task<decimal> RiceStock(Data.SmartRationDbContext db, int shopId) =>
        db.Inventory.Where(i => i.RationShopId == shopId && i.RationType == RationType.Rice).Select(i => i.AvailableQuantity).SingleAsync();

    [Fact]
    public async Task QuickComplete_WithinEntitlement_SucceedsThroughSharedPipeline()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            var (_, shop) = Build(db, scenario.Shop.Id);

            var token = await shop.CompleteCollectionAsync(scenario.Token.Id);

            Assert.Equal("Completed", token.Status);
            Assert.Equal(95, await RiceStock(db, scenario.Shop.Id));
            // Same receipt + ledger as the QR path.
            Assert.Equal("QUEUE", (await db.RationCollections.SingleAsync()).VerificationMethod);
            Assert.Equal(1, await db.InventoryMovements.CountAsync());
        }
    }

    [Fact]
    public async Task QrConfirm_AboveEntitlement_Returns400AndChangesNothing()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceQuotaPerMember: 5, riceInventory: 100);
            await SetRiceRequest(db, scenario.Token.Id, 6);
            var (graph, _) = Build(db, scenario.Shop.Id);

            var ex = await Assert.ThrowsAsync<BadRequestException>(() => graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR"));

            Assert.Equal("ENTITLEMENT_EXCEEDED", ex.ErrorCode);
            Assert.Equal("Requested quantity exceeds the beneficiary entitlement.", ex.Message);
            Assert.Equal(100, await RiceStock(db, scenario.Shop.Id));
            Assert.Equal(0, await db.RationCollections.CountAsync());
            Assert.Equal(0, await db.InventoryMovements.CountAsync());
        }
    }

    [Fact]
    public async Task QuickComplete_AboveEntitlement_IsRejectedToo()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceQuotaPerMember: 5, riceInventory: 100);
            await SetRiceRequest(db, scenario.Token.Id, 50);
            var (_, shop) = Build(db, scenario.Shop.Id);

            var ex = await Assert.ThrowsAsync<BadRequestException>(() => shop.CompleteCollectionAsync(scenario.Token.Id));

            Assert.Equal("ENTITLEMENT_EXCEEDED", ex.ErrorCode);
            Assert.Equal(100, await RiceStock(db, scenario.Shop.Id));
            Assert.Equal(TokenStatus.Confirmed, (await db.Tokens.SingleAsync(t => t.Id == scenario.Token.Id)).Status);
        }
    }

    [Fact]
    public async Task QuickComplete_OtherShop_IsForbidden()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var (_, shop) = Build(db, scenario.Shop.Id + 1);

            await Assert.ThrowsAsync<ForbiddenException>(() => shop.CompleteCollectionAsync(scenario.Token.Id));
        }
    }

    [Fact]
    public async Task InsufficientStockForOneItem_NothingIsDeducted()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            // Entitled to wheat too, but the shop only has 1 kg of it.
            db.SchemeEntitlementItems.Add(new SchemeEntitlementItem { RationSchemeId = scenario.Scheme.Id, RationType = RationType.Wheat, QuotaPerEligibleMemberPerMonth = 5 });
            db.Inventory.Add(new Inventory { RationShopId = scenario.Shop.Id, RationType = RationType.Wheat, AvailableQuantity = 1, MinimumStockLevel = 10 });
            db.TokenItems.Add(new TokenItem { TokenId = scenario.Token.Id, RationType = RationType.Wheat, Quantity = 3 });
            await db.SaveChangesAsync();
            var (graph, _) = Build(db, scenario.Shop.Id);

            var ex = await Assert.ThrowsAsync<ConflictException>(() => graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR"));

            Assert.Equal("INSUFFICIENT_STOCK", ex.ErrorCode);
            Assert.Equal(100, await RiceStock(db, scenario.Shop.Id)); // rice was in stock but must not be issued alone
            Assert.Equal(0, await db.InventoryMovements.CountAsync());
            Assert.Equal(0, await db.RationCollections.CountAsync());
        }
    }

    [Fact]
    public async Task UnknownToken_IsNotFound()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var (graph, _) = Build(db, scenario.Shop.Id);

            await Assert.ThrowsAsync<NotFoundException>(() => graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id + 999, "QR"));
        }
    }

    [Fact]
    public async Task ExpiredToken_IsBlocked()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            scenario.Slot.SlotDate = DateTime.UtcNow.Date.AddDays(-2);
            await db.SaveChangesAsync();
            var (graph, _) = Build(db, scenario.Shop.Id);

            var ex = await Assert.ThrowsAsync<ConflictException>(() => graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR"));

            Assert.Contains("expired", ex.Message, StringComparison.OrdinalIgnoreCase);
            Assert.Equal(100, await RiceStock(db, scenario.Shop.Id));
        }
    }

    [Fact]
    public async Task BlockedBeneficiary_IsRejected()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            scenario.Beneficiary.IsBlocked = true;
            await db.SaveChangesAsync();
            var (graph, _) = Build(db, scenario.Shop.Id);

            await Assert.ThrowsAsync<ConflictException>(() => graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR"));
            Assert.Equal(100, await RiceStock(db, scenario.Shop.Id));
        }
    }

    [Fact]
    public async Task QuickComplete_RetriedWithSameKey_DeductsOnce()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            var (graph, shop) = Build(db, scenario.Shop.Id);

            await shop.CompleteCollectionAsync(scenario.Token.Id, "queue-retry-1");
            // Network retry of the SAME request through the same endpoint: succeeds, no second issue.
            var retried = await shop.CompleteCollectionAsync(scenario.Token.Id, "queue-retry-1");
            // A different request for the used token is still refused.
            await Assert.ThrowsAsync<ConflictException>(() => shop.CompleteCollectionAsync(scenario.Token.Id, "queue-retry-2"));

            Assert.Equal("Completed", retried.Status);
            Assert.Equal(95, await RiceStock(db, scenario.Shop.Id));
            Assert.Equal(1, await db.RationCollections.CountAsync());
        }
    }

    [Fact]
    public void EntitlementCheck_RejectsNegativeAndOutOfSchemeItems()
    {
        var service = new EntitlementService(null!);
        var entitlement = new EntitlementSummaryDto
        {
            Items = [new EntitlementItemDto { RationType = "Rice", TodayAllocation = 5 }]
        };

        Assert.Equal("INVALID_QUANTITY", Assert.Throws<BadRequestException>(() =>
            service.EnsureRequestWithinEntitlement(entitlement, [(RationType.Rice, -1m)])).ErrorCode);
        Assert.Equal("ENTITLEMENT_EXCEEDED", Assert.Throws<BadRequestException>(() =>
            service.EnsureRequestWithinEntitlement(entitlement, [(RationType.Sugar, 1m)])).ErrorCode);
        service.EnsureRequestWithinEntitlement(entitlement, [(RationType.Rice, 5m)]);
    }
}
