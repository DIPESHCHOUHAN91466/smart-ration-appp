using Microsoft.Extensions.Options;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

public class QrServiceTests
{
    private static QrService BuildService(Data.SmartRationDbContext db, FakeCurrentUserService currentUser) =>
        new(db, Options.Create(new QrOptions { Secret = "test-secret-value-not-for-production" }), currentUser);

    // Scenario 1: Valid QR.
    [Fact]
    public async Task VerifyAsync_ValidSignedQr_ReturnsToken()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var currentUser = new FakeCurrentUserService { UserId = 999, Role = UserRole.GovernmentOfficial };
            var qr = BuildService(db, currentUser);

            var qrValue = qr.ComputeQrValue(scenario.Token.Id, scenario.Token.TokenNumber);
            var result = await qr.VerifyAsync(qrValue);

            Assert.Equal(scenario.Token.TokenNumber, result.TokenNumber);
        }
    }

    // Scenario 2: Invalid QR.
    [Fact]
    public async Task VerifyAsync_TamperedSignature_ThrowsBadRequest()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var currentUser = new FakeCurrentUserService { UserId = 999, Role = UserRole.GovernmentOfficial };
            var qr = BuildService(db, currentUser);

            var tampered = $"SRQR-{scenario.Token.Id}-0000000000000000";

            await Assert.ThrowsAsync<BadRequestException>(() => qr.VerifyAsync(tampered));
        }
    }

    [Fact]
    public async Task VerifyAsync_UnknownFormat_ThrowsBadRequest()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            ScenarioBuilder.SeedBasicScenario(db);
            var currentUser = new FakeCurrentUserService { UserId = 999, Role = UserRole.GovernmentOfficial };
            var qr = BuildService(db, currentUser);

            await Assert.ThrowsAsync<BadRequestException>(() => qr.VerifyAsync("not-a-qr-code"));
        }
    }

    // Scenario 4: Already-used QR.
    [Fact]
    public async Task VerifyAsync_CompletedToken_ThrowsConflict()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, tokenStatus: TokenStatus.Completed);
            var currentUser = new FakeCurrentUserService { UserId = 999, Role = UserRole.GovernmentOfficial };
            var qr = BuildService(db, currentUser);
            var qrValue = qr.ComputeQrValue(scenario.Token.Id, scenario.Token.TokenNumber);

            await Assert.ThrowsAsync<ConflictException>(() => qr.VerifyAsync(qrValue));
        }
    }

    // ResolveTokenForVerificationAsync (used by the rich verification flow) does NOT
    // reject a completed token — it lets the caller show a "blocked" screen instead.
    [Fact]
    public async Task ResolveTokenForVerificationAsync_CompletedToken_DoesNotThrow()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, tokenStatus: TokenStatus.Completed);
            var currentUser = new FakeCurrentUserService { UserId = 999, Role = UserRole.GovernmentOfficial };
            var qr = BuildService(db, currentUser);
            var qrValue = qr.ComputeQrValue(scenario.Token.Id, scenario.Token.TokenNumber);

            var token = await qr.ResolveTokenForVerificationAsync(qrValue);

            Assert.Equal(TokenStatus.Completed, token.Status);
        }
    }

    // Scenario 20: Shop authorization.
    [Fact]
    public async Task ResolveTokenForVerificationAsync_ShopOwnerFromDifferentShop_ThrowsForbidden()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var currentUser = new FakeCurrentUserService { UserId = 999, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id + 999 };
            var qr = BuildService(db, currentUser);
            var qrValue = qr.ComputeQrValue(scenario.Token.Id, scenario.Token.TokenNumber);

            await Assert.ThrowsAsync<ForbiddenException>(() => qr.ResolveTokenForVerificationAsync(qrValue));
        }
    }

    [Fact]
    public async Task ResolveTokenForVerificationAsync_ShopOwnerFromSameShop_Succeeds()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var currentUser = new FakeCurrentUserService { UserId = 999, Role = UserRole.ShopOwner, RationShopId = scenario.Shop.Id };
            var qr = BuildService(db, currentUser);
            var qrValue = qr.ComputeQrValue(scenario.Token.Id, scenario.Token.TokenNumber);

            var token = await qr.ResolveTokenForVerificationAsync(qrValue);

            Assert.Equal(scenario.Token.Id, token.Id);
        }
    }
}
