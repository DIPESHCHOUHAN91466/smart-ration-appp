using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Inventory;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

// Low-bandwidth retry safety (Idempotency-Key) and the inventory movement ledger.
public class InventoryLedgerAndIdempotencyTests
{
    [Fact]
    public async Task Confirm_RetriedWithSameKey_ReturnsSameReceiptAndIssuesOnce()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            var graph = new TestServiceGraph(db, new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id });

            var first = await graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR", "retry-key-001");
            var second = await graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR", "retry-key-001");

            Assert.Equal(first.CollectionCode, second.CollectionCode);
            Assert.Equal(first.TotalQuantityKg, second.TotalQuantityKg);
            Assert.Equal(1, await db.RationCollections.CountAsync());

            var rice = await db.Inventory.FirstAsync(i => i.RationShopId == scenario.Shop.Id && i.RationType == RationType.Rice);
            Assert.Equal(95, rice.AvailableQuantity);
        }
    }

    [Fact]
    public async Task Confirm_WithoutKey_SecondCallStillRejected()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var graph = new TestServiceGraph(db, new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id });

            await graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR");
            await Assert.ThrowsAsync<ConflictException>(() => graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR"));
        }
    }

    [Fact]
    public async Task Confirm_KeyReusedForDifferentToken_IsRejected()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var graph = new TestServiceGraph(db, new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id });

            await graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR", "shared-key");

            var ex = await Assert.ThrowsAsync<ConflictException>(() =>
                graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id + 1, "QR", "shared-key"));
            Assert.Equal("IDEMPOTENCY_KEY_REUSED", ex.ErrorCode);
        }
    }

    [Fact]
    public async Task Confirm_WritesDistributedMovementMatchingBalance()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            var graph = new TestServiceGraph(db, new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id });

            await graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR");

            var movement = await db.InventoryMovements.SingleAsync();
            Assert.Equal(InventoryMovementType.Distributed, movement.MovementType);
            Assert.Equal(RationType.Rice, movement.RationType);
            Assert.Equal(5, movement.Quantity);
            Assert.Equal(95, movement.BalanceAfter);
            Assert.Equal(scenario.Token.TokenNumber, movement.Reference);
        }
    }

    [Fact]
    public async Task Confirm_InsufficientStock_RollsBackWithoutLedgerRows()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 0);
            var graph = new TestServiceGraph(db, new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id });

            await Assert.ThrowsAsync<ConflictException>(() => graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR"));

            Assert.Equal(0, await db.InventoryMovements.CountAsync());
            Assert.Equal(0, await db.RationCollections.CountAsync());
        }
    }

    [Fact]
    public async Task ReceiveAndDamage_UpdateBalanceAndLedger()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            var currentUser = new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id };
            var service = new InventoryService(db, currentUser, new TestServiceGraph(db, currentUser).Notifications);
            var rice = await db.Inventory.FirstAsync(i => i.RationShopId == scenario.Shop.Id && i.RationType == RationType.Rice);

            await service.ReceiveStockAsync(rice.Id, new StockMovementRequestDto { Quantity = 50, Reference = "CHALLAN-42" });
            await service.RecordDamageAsync(rice.Id, new StockMovementRequestDto { Quantity = 10, Note = "Water damage" });

            Assert.Equal(140, rice.AvailableQuantity);
            var movements = await db.InventoryMovements.OrderBy(m => m.Id).ToListAsync();
            Assert.Equal([InventoryMovementType.Received, InventoryMovementType.Damaged], movements.Select(m => m.MovementType));
            Assert.Equal([150m, 140m], movements.Select(m => m.BalanceAfter));
        }
    }

    [Fact]
    public async Task Damage_MoreThanStock_IsRejected()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 5);
            var currentUser = new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id };
            var service = new InventoryService(db, currentUser, new TestServiceGraph(db, currentUser).Notifications);
            var rice = await db.Inventory.FirstAsync(i => i.RationShopId == scenario.Shop.Id && i.RationType == RationType.Rice);

            var ex = await Assert.ThrowsAsync<BadRequestException>(() => service.RecordDamageAsync(rice.Id, new StockMovementRequestDto { Quantity = 6 }));
            Assert.Equal("INSUFFICIENT_STOCK", ex.ErrorCode);
            Assert.Equal(5, rice.AvailableQuantity);
        }
    }

    [Fact]
    public async Task ReceiveStock_OtherShop_IsForbidden()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var currentUser = new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id + 1 };
            var service = new InventoryService(db, currentUser, new TestServiceGraph(db, currentUser).Notifications);
            var rice = await db.Inventory.FirstAsync(i => i.RationShopId == scenario.Shop.Id);

            await Assert.ThrowsAsync<ForbiddenException>(() => service.ReceiveStockAsync(rice.Id, new StockMovementRequestDto { Quantity = 1 }));
        }
    }
}
