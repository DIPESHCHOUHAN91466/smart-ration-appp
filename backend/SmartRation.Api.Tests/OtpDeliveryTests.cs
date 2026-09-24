using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Sms;
using SmartRation.Api.Services.Verification;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

// OTP delivery through ISmsProvider, resend cooldown, and "only the newest code works".
public class OtpDeliveryTests
{
    private class RecordingSms(bool succeed = true) : ISmsProvider
    {
        public List<(string Phone, string Message)> Sent { get; } = [];
        public string Name => "Recording";

        public Task<SmsSendResult> SendAsync(string phone, string message, CancellationToken ct = default)
        {
            Sent.Add((phone, message));
            return Task.FromResult(new SmsSendResult(succeed, Name, Error: succeed ? null : "down"));
        }
    }

    private static SyntheticOtpService Build(Data.SmartRationDbContext db, ISmsProvider sms, int cooldown = 30) =>
        new(db, Options.Create(new DemoModeOptions { DemoOtpEnabled = true, DemoOtpValue = "123456", OtpExpiryMinutes = 5, OtpMaxAttempts = 3, OtpResendCooldownSeconds = cooldown }), sms);

    [Fact]
    public async Task Request_SendsCodeToBeneficiaryMobile()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var sms = new RecordingSms();

            await Build(db, sms).RequestOtpAsync(scenario.Beneficiary.Id, 1);

            var (phone, message) = Assert.Single(sms.Sent);
            Assert.Equal(scenario.BeneficiaryUser.MobileNumber, phone);
            Assert.Contains("123456", message);
        }
    }

    [Fact]
    public async Task Request_WithinCooldown_IsRejected()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var service = Build(db, new RecordingSms());

            await service.RequestOtpAsync(scenario.Beneficiary.Id, 1);
            var ex = await Assert.ThrowsAsync<BadRequestException>(() => service.RequestOtpAsync(scenario.Beneficiary.Id, 1));

            Assert.Equal("OTP_COOLDOWN", ex.ErrorCode);
        }
    }

    [Fact]
    public async Task Resend_ExpiresThePreviousCode()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);
            var service = Build(db, new RecordingSms(), cooldown: 0);

            var first = await service.RequestOtpAsync(scenario.Beneficiary.Id, 1);
            var second = await service.RequestOtpAsync(scenario.Beneficiary.Id, 1);

            Assert.Equal(OtpStatus.Expired, (await db.OtpVerifications.SingleAsync(o => o.Id == first.Id)).Status);
            await Assert.ThrowsAsync<BadRequestException>(() => service.VerifyOtpAsync(first.Id, "123456"));
            Assert.Equal(OtpStatus.Verified, (await service.VerifyOtpAsync(second.Id, "123456")).Status);
        }
    }

    [Fact]
    public async Task SmsFailure_Returns503AndCodeIsUnusable()
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db);

            var ex = await Assert.ThrowsAsync<ServiceUnavailableException>(() => Build(db, new RecordingSms(succeed: false)).RequestOtpAsync(scenario.Beneficiary.Id, 1));

            Assert.Equal("SMS_UNAVAILABLE", ex.ErrorCode);
            Assert.Equal(OtpStatus.Failed, (await db.OtpVerifications.SingleAsync()).Status);
        }
    }

    [Fact]
    public async Task MockProvider_ReportsSentWithoutDelivering()
    {
        var result = await new MockSmsProvider(NullLogger<MockSmsProvider>.Instance).SendAsync("9876543210", "code 123456");
        Assert.True(result.Sent);
        Assert.Equal("Mock", result.Provider);
    }

    [Fact]
    public async Task HttpProvider_Unconfigured_FailsSafely()
    {
        var provider = new HttpSmsProvider(new HttpClient(), Options.Create(new SmsOptions { Provider = "Http" }), NullLogger<HttpSmsProvider>.Instance);
        var result = await provider.SendAsync("9876543210", "hello");
        Assert.False(result.Sent);
    }
}
