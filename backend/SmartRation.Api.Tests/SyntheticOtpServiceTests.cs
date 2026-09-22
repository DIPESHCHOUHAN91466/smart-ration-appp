using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

public class SyntheticOtpServiceTests
{
    private static SyntheticOtpService BuildService(Data.SmartRationDbContext db, DemoModeOptions? options = null) =>
        new(db, Options.Create(options ?? new DemoModeOptions { DemoOtpEnabled = true, DemoOtpValue = "123456", OtpExpiryMinutes = 5, OtpMaxAttempts = 3 }));

    // Scenario 11: OTP request.
    [Fact]
    public async Task RequestOtpAsync_ActiveBeneficiary_CreatesPendingRecord()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var otp = BuildService(db);

            var record = await otp.RequestOtpAsync(scenario.Beneficiary.Id, requestedByUserId: 1);

            Assert.Equal(OtpStatus.Pending, record.Status);
            Assert.Equal(0, record.AttemptCount);
        }
    }

    [Fact]
    public async Task RequestOtpAsync_BlockedBeneficiary_ThrowsForbidden()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            scenario.Beneficiary.IsBlocked = true;
            await db.SaveChangesAsync();
            var otp = BuildService(db);

            await Assert.ThrowsAsync<ForbiddenException>(() => otp.RequestOtpAsync(scenario.Beneficiary.Id, 1));
        }
    }

    // Scenario 12: OTP verification (success).
    [Fact]
    public async Task VerifyOtpAsync_CorrectDemoCode_MarksVerified()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var otp = BuildService(db);
            var record = await otp.RequestOtpAsync(scenario.Beneficiary.Id, 1);

            var verified = await otp.VerifyOtpAsync(record.Id, "123456");

            Assert.Equal(OtpStatus.Verified, verified.Status);
            Assert.NotNull(verified.VerifiedAt);
        }
    }

    // Scenario 13: Wrong OTP.
    [Fact]
    public async Task VerifyOtpAsync_WrongCode_ThrowsAndIncrementsAttempts()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var otp = BuildService(db);
            var record = await otp.RequestOtpAsync(scenario.Beneficiary.Id, 1);

            await Assert.ThrowsAsync<BadRequestException>(() => otp.VerifyOtpAsync(record.Id, "000000"));

            var reloaded = await db.OtpVerifications.FirstAsync(o => o.Id == record.Id);
            Assert.Equal(1, reloaded.AttemptCount);
            Assert.Equal(OtpStatus.Pending, reloaded.Status);
        }
    }

    // Scenario 15: Maximum OTP attempts.
    [Fact]
    public async Task VerifyOtpAsync_ExceedsMaxAttempts_MarksFailedAndRejectsFurtherAttempts()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var otp = BuildService(db, new DemoModeOptions { DemoOtpEnabled = true, DemoOtpValue = "123456", OtpExpiryMinutes = 5, OtpMaxAttempts = 3 });
            var record = await otp.RequestOtpAsync(scenario.Beneficiary.Id, 1);

            for (var i = 0; i < 3; i++)
            {
                await Assert.ThrowsAsync<BadRequestException>(() => otp.VerifyOtpAsync(record.Id, "000000"));
            }

            var reloaded = await db.OtpVerifications.FirstAsync(o => o.Id == record.Id);
            Assert.Equal(OtpStatus.Failed, reloaded.Status);

            // A 4th attempt — even with the correct code — must still be rejected.
            var ex = await Assert.ThrowsAsync<BadRequestException>(() => otp.VerifyOtpAsync(record.Id, "123456"));
            Assert.Contains("Failed", ex.Message);
        }
    }

    // Scenario 14: Expired OTP.
    [Fact]
    public async Task VerifyOtpAsync_AfterExpiry_ThrowsAndMarksExpired()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var otp = BuildService(db);
            var record = await otp.RequestOtpAsync(scenario.Beneficiary.Id, 1);

            record.ExpiresAt = DateTime.UtcNow.AddMinutes(-1);
            await db.SaveChangesAsync();

            await Assert.ThrowsAsync<BadRequestException>(() => otp.VerifyOtpAsync(record.Id, "123456"));

            var reloaded = await db.OtpVerifications.FirstAsync(o => o.Id == record.Id);
            Assert.Equal(OtpStatus.Expired, reloaded.Status);
        }
    }
}
