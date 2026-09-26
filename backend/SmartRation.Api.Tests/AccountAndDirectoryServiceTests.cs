using Microsoft.Extensions.Options;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Users;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

// The rules that moved out of UsersController, FamiliesController, PublicController, ShopsController,
// AuditController and VerificationController into services (Phase C of the third audit).
public class AccountAndDirectoryServiceTests
{
    private static User AddUser(SmartRationDbContext db, UserRole role, string? mobile = null)
    {
        var user = new User { FullName = $"{role} User", Email = $"u{Guid.NewGuid():N}@example.com", MobileNumber = mobile ?? ScenarioBuilder.NextSyntheticMobile(), PasswordHash = "x", Role = role, IsActive = true };
        db.Users.Add(user);
        db.SaveChanges();
        return user;
    }

    // ---- UserAccountService ----

    [Fact]
    public async Task UpdateOwnProfile_TrimsAndSaves()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var me = AddUser(db, UserRole.RuralUser);
            var service = new UserAccountService(db, new FakeCurrentUserService { UserId = me.Id, Role = UserRole.RuralUser });
            var newMobile = ScenarioBuilder.NextSyntheticMobile();

            var result = await service.UpdateOwnProfileAsync(new UpdateProfileRequestDto { FullName = "  New Name ", MobileNumber = $" {newMobile} " });

            Assert.Equal("New Name", result.FullName);
            Assert.Equal(newMobile, (await db.Users.FindAsync(me.Id))!.MobileNumber);
        }
    }

    // Regression: the uniqueness check used the raw (untrimmed) input, so a padded duplicate
    // slipped past it and hit the unique index as a 500 instead of a 409.
    [Fact]
    public async Task UpdateOwnProfile_PaddedDuplicateMobile_IsConflict()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var other = AddUser(db, UserRole.RuralUser);
            var me = AddUser(db, UserRole.RuralUser);
            var service = new UserAccountService(db, new FakeCurrentUserService { UserId = me.Id, Role = UserRole.RuralUser });

            await Assert.ThrowsAsync<ConflictException>(() =>
                service.UpdateOwnProfileAsync(new UpdateProfileRequestDto { FullName = "Me", MobileNumber = $"  {other.MobileNumber} " }));
        }
    }

    [Fact]
    public async Task UpdateOwnProfile_KeepingOwnMobile_IsAllowed()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var me = AddUser(db, UserRole.RuralUser);
            var service = new UserAccountService(db, new FakeCurrentUserService { UserId = me.Id, Role = UserRole.RuralUser });

            var result = await service.UpdateOwnProfileAsync(new UpdateProfileRequestDto { FullName = "Same Mobile", MobileNumber = me.MobileNumber });
            Assert.Equal("Same Mobile", result.FullName);
        }
    }

    [Fact]
    public async Task ListUsers_FiltersByRole_AndRejectsUnknownRole()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            AddUser(db, UserRole.RuralUser);
            AddUser(db, UserRole.ShopOwner);
            var service = new UserAccountService(db, new FakeCurrentUserService { UserId = 1, Role = UserRole.Admin });

            Assert.Equal(2, (await service.ListUsersAsync(null)).Count);
            Assert.Single(await service.ListUsersAsync("shopowner"));
            await Assert.ThrowsAsync<BadRequestException>(() => service.ListUsersAsync("Superuser"));
        }
    }

    // ---- FamilyService (shared BeneficiaryAccess rule) ----

    [Fact]
    public async Task Family_OwnerAndStaffCanRead_OtherCitizenIsForbidden()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var graph = new TestServiceGraph(db, new FakeCurrentUserService());
            FamilyService As(int userId, UserRole role) => new(db, graph.Entitlement, new FakeCurrentUserService { UserId = userId, Role = role });

            Assert.Equal(scenario.Family.FamilyCode, (await As(scenario.BeneficiaryUser.Id, UserRole.RuralUser).GetFamilyAsync(scenario.Family.Id)).FamilyCode);
            Assert.Equal(scenario.Family.FamilyCode, (await As(999, UserRole.GovernmentOfficial).GetFamilyAsync(scenario.Family.Id)).FamilyCode);

            var stranger = AddUser(db, UserRole.RuralUser);
            await Assert.ThrowsAsync<ForbiddenException>(() => As(stranger.Id, UserRole.RuralUser).GetFamilyAsync(scenario.Family.Id));
            await Assert.ThrowsAsync<ForbiddenException>(() => As(stranger.Id, UserRole.RuralUser).GetEntitlementAsync(scenario.Family.Id));
            await Assert.ThrowsAsync<NotFoundException>(() => As(999, UserRole.Admin).GetFamilyAsync(424242));
        }
    }

    // ---- PublicProfileService (anonymous) ----

    [Fact]
    public async Task PublicProfile_ExposesOnlyNonSensitiveFields()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var profile = await new PublicProfileService(db).GetAsync(scenario.Beneficiary.BeneficiaryCode);

            Assert.Equal("Eligible", profile.EligibilityBadge);
            Assert.Equal("Verified", profile.VerificationBadge);
            Assert.Equal(scenario.Shop.ShopCode, profile.ShopCode);

            // The DTO must never grow a sensitive field: fail loudly if someone adds one.
            var forbidden = new[] { "aadhaar", "mobile", "phone", "email", "address", "member", "password", "name" };
            var leaking = typeof(DTOs.Verification.PublicBeneficiaryProfileDto).GetProperties()
                .Select(p => p.Name.ToLowerInvariant())
                .Where(n => forbidden.Any(f => n.Contains(f)))
                .ToList();
            Assert.Empty(leaking);

            await Assert.ThrowsAsync<NotFoundException>(() => new PublicProfileService(db).GetAsync("BEN-DOES-NOT-EXIST"));
        }
    }

    // ---- ShopDirectoryService ----

    [Fact]
    public async Task ShopDirectory_ListsOnlyActiveShops()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            db.RationShops.Add(new RationShop { ShopName = "Closed Shop", ShopCode = "SHOP-TEST-002", Address = "Test", District = "Test", State = "Test", IsActive = false });
            db.SaveChanges();

            var shops = await new ShopDirectoryService(db).GetActiveShopsAsync();
            Assert.Equal(new[] { scenario.Shop.ShopCode }, shops.Select(s => s.ShopCode));
        }
    }

    // ---- VerificationAuditService.QueryAsync ----

    [Fact]
    public async Task AuditQuery_FiltersAndClampsTake()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            for (var i = 0; i < 3; i++)
            {
                db.VerificationAuditLogs.Add(new VerificationAuditLog { ShopId = 1, BeneficiaryId = 10, Action = VerificationAction.QrScanned, VerificationMethod = "QR", Status = i == 0 ? "FAILED" : "SUCCESS", Timestamp = DateTime.UtcNow.AddMinutes(-i) });
            }
            db.VerificationAuditLogs.Add(new VerificationAuditLog { ShopId = 2, BeneficiaryId = 20, Action = VerificationAction.QrScanned, VerificationMethod = "QR", Status = "SUCCESS", Timestamp = DateTime.UtcNow });
            db.SaveChanges();
            var audit = new TestServiceGraph(db, new FakeCurrentUserService()).VerificationAudit;

            Assert.Equal(3, (await audit.QueryAsync(shopId: 1, null, null, 100)).Count);
            Assert.Single(await audit.QueryAsync(null, beneficiaryId: 20, null, 100));
            Assert.Single(await audit.QueryAsync(shopId: 1, null, "FAILED", 100));
            Assert.Single(await audit.QueryAsync(null, null, null, take: 0)); // clamped up to 1
            Assert.Equal(4, (await audit.QueryAsync(null, null, null, take: 100000)).Count); // clamped to 500
        }
    }

    // ---- SyntheticOtpService.RequestOtpForMobileAsync ----

    [Fact]
    public async Task OtpByMobile_KnownMobileCreatesOtp_UnknownIsNotFound()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var otp = new SyntheticOtpService(db, Options.Create(new DemoModeOptions { DemoOtpEnabled = true, DemoOtpValue = "123456", OtpExpiryMinutes = 5, OtpMaxAttempts = 3 }));

            var record = await otp.RequestOtpForMobileAsync(scenario.BeneficiaryUser.MobileNumber, requestedByUserId: 1);
            Assert.Equal(scenario.Beneficiary.Id, record.BeneficiaryId);

            await Assert.ThrowsAsync<NotFoundException>(() => otp.RequestOtpForMobileAsync("9098999999", requestedByUserId: 1));
        }
    }
}
