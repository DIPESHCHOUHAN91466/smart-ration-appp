using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Models;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

public class RationCollectionServiceTests
{
    // Scenario 5 + 17: Valid beneficiary, inventory decrement.
    [Fact]
    public async Task ConfirmCollectionAsync_ValidToken_DecrementsInventoryAndRecordsReceipt()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            var currentUser = new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id };
            var graph = new TestServiceGraph(db, currentUser);
            var collectionService = graph.BuildCollectionService();

            var receipt = await collectionService.ConfirmCollectionAsync(scenario.Token.Id, "QR");

            Assert.StartsWith("COL-DEMO-", receipt.CollectionCode);
            Assert.Equal(5, receipt.TotalQuantityKg);

            var inventory = await db.Inventory.FirstAsync(i => i.RationShopId == scenario.Shop.Id && i.RationType == RationType.Rice);
            Assert.Equal(95, inventory.AvailableQuantity);
            Assert.Equal(5, inventory.AllocatedQuantity);

            var token = await db.Tokens.FirstAsync(t => t.Id == scenario.Token.Id);
            Assert.Equal(TokenStatus.Completed, token.Status);
            Assert.NotNull(token.CollectedAt);
        }
    }

    // Scenario 18: Duplicate collection prevention.
    [Fact]
    public async Task ConfirmCollectionAsync_CalledTwice_SecondCallIsRejectedAndInventoryNotDoubleDeducted()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceInventory: 100);
            var currentUser = new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id };
            var graph = new TestServiceGraph(db, currentUser);

            await graph.BuildCollectionService().ConfirmCollectionAsync(scenario.Token.Id, "QR");

            // Fresh service instance, same underlying DB — mirrors a second, separate HTTP request.
            var secondAttempt = new TestServiceGraph(db, currentUser).BuildCollectionService();
            await Assert.ThrowsAsync<ConflictException>(() => secondAttempt.ConfirmCollectionAsync(scenario.Token.Id, "QR"));

            var inventory = await db.Inventory.FirstAsync(i => i.RationShopId == scenario.Shop.Id && i.RationType == RationType.Rice);
            Assert.Equal(95, inventory.AvailableQuantity); // unchanged by the rejected second attempt

            var collectionsCount = await db.RationCollections.CountAsync(c => c.TokenId == scenario.Token.Id);
            Assert.Equal(1, collectionsCount);
        }
    }

    [Fact]
    public async Task ConfirmCollectionAsync_AadhaarNotVerified_IsBlockedAndInventoryUntouched()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, aadhaarStatus: AadhaarVerificationStatus.Pending, riceInventory: 100);
            var currentUser = new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id };
            var collectionService = new TestServiceGraph(db, currentUser).BuildCollectionService();

            var ex = await Assert.ThrowsAsync<ConflictException>(() => collectionService.ConfirmCollectionAsync(scenario.Token.Id, "QR"));
            Assert.Contains("Aadhaar", ex.Message);

            var inventory = await db.Inventory.FirstAsync(i => i.RationShopId == scenario.Shop.Id && i.RationType == RationType.Rice);
            Assert.Equal(100, inventory.AvailableQuantity);

            var token = await db.Tokens.FirstAsync(t => t.Id == scenario.Token.Id);
            Assert.Equal(TokenStatus.Confirmed, token.Status);
        }
    }

    [Fact]
    public async Task ConfirmCollectionAsync_NoRemainingEntitlement_IsBlocked()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, riceQuotaPerMember: 5, riceInventory: 100);

            // Beneficiary already collected their full monthly entitlement this month.
            db.RationCollections.Add(new RationCollection
            {
                CollectionCode = "COL-TEST-PRIOR",
                TokenId = scenario.Token.Id,
                BeneficiaryId = scenario.Beneficiary.Id,
                RationShopId = scenario.Shop.Id,
                OperatorUserId = 1,
                VerificationMethod = "QR",
                CollectedAt = DateTime.UtcNow,
                Items = [new RationCollectionItem { RationType = RationType.Rice, Quantity = 5 }]
            });
            // Give the token a fresh, still-Confirmed sibling so this isn't just the "already used" case.
            var slot2 = new TimeSlot { RationShopId = scenario.Shop.Id, SlotDate = DateTime.UtcNow.Date, StartTime = TimeSpan.FromHours(10), EndTime = TimeSpan.FromHours(10).Add(TimeSpan.FromMinutes(5)), Capacity = 5, BookedCount = 1 };
            db.TimeSlots.Add(slot2);
            await db.SaveChangesAsync();
            var token2 = new Token { TokenNumber = "SR-TEST-000002", UserId = scenario.BeneficiaryUser.Id, RationShopId = scenario.Shop.Id, TimeSlotId = slot2.Id, Status = TokenStatus.Confirmed, CreatedAt = DateTime.UtcNow };
            db.Tokens.Add(token2);
            await db.SaveChangesAsync();
            db.TokenItems.Add(new TokenItem { TokenId = token2.Id, RationType = RationType.Rice, Quantity = 5 });
            await db.SaveChangesAsync();

            var currentUser = new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id };
            var collectionService = new TestServiceGraph(db, currentUser).BuildCollectionService();

            var ex = await Assert.ThrowsAsync<ConflictException>(() => collectionService.ConfirmCollectionAsync(token2.Id, "QR"));
            Assert.Contains("entitlement", ex.Message, StringComparison.OrdinalIgnoreCase);
        }
    }

    [Fact]
    public async Task ConfirmCollectionAsync_ShopOwnerFromDifferentShop_ThrowsForbidden()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var currentUser = new FakeCurrentUserService { UserId = 1, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id + 999 };
            var collectionService = new TestServiceGraph(db, currentUser).BuildCollectionService();

            await Assert.ThrowsAsync<ForbiddenException>(() => collectionService.ConfirmCollectionAsync(scenario.Token.Id, "QR"));
        }
    }
}
