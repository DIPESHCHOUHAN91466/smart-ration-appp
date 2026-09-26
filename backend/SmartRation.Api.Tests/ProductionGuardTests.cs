using SmartRation.Api.Configuration;

namespace SmartRation.Api.Tests;

// Outside Development: no fixed demo OTP, and no silent mock SMS - except the explicit synthetic-demo opt-in.
public class ProductionGuardTests
{
    private static DemoModeOptions Demo(bool demoOtp = false) => new() { DemoOtpEnabled = demoOtp };

    [Fact]
    public void Development_AllowsEverything()
    {
        Assert.Empty(ProductionGuard.Problems(true, DataMode.Synthetic, Demo(demoOtp: true), new SmsOptions { Provider = "Mock" }));
    }

    [Fact]
    public void Production_WithRealGateway_Starts()
    {
        Assert.Empty(ProductionGuard.Problems(false, DataMode.Synthetic, Demo(), new SmsOptions { Provider = "Http" }));
    }

    [Fact]
    public void Production_RefusesDemoOtp_AndSilentMockSms()
    {
        var problems = ProductionGuard.Problems(false, DataMode.Synthetic, Demo(demoOtp: true), new SmsOptions { Provider = "Mock" });
        Assert.Equal(2, problems.Count);
        Assert.Contains(problems, p => p.Contains("DemoOtpEnabled"));
        Assert.Contains(problems, p => p.Contains("Sms:Provider"));
    }

    [Fact]
    public void SyntheticDemo_MayOptIntoMockSms()
    {
        var sms = new SmsOptions { Provider = "Mock", AllowMockOutsideDevelopment = true };
        Assert.Empty(ProductionGuard.Problems(false, DataMode.Synthetic, Demo(), sms));
        Assert.True(ProductionGuard.UsesSyntheticDemoSms(false, DataMode.Synthetic, sms));
    }

    [Fact]
    public void RealData_NeverAllowsMockSms_EvenWithTheOptIn()
    {
        var sms = new SmsOptions { Provider = "Mock", AllowMockOutsideDevelopment = true };
        Assert.Single(ProductionGuard.Problems(false, DataMode.Real, Demo(), sms));
        Assert.False(ProductionGuard.UsesSyntheticDemoSms(false, DataMode.Real, sms));
    }
}
