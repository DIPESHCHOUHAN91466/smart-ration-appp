using SmartRation.Api.Configuration;
using Xunit;

namespace SmartRation.Api.Tests;

public class DataModeGuardTests
{
    [Theory]
    [InlineData(null, null, DataMode.Synthetic)]
    [InlineData("", "Real", DataMode.Real)]
    [InlineData("synthetic", "Real", DataMode.Synthetic)]   // the environment variable wins
    [InlineData("REAL", null, DataMode.Real)]
    public void Resolve_reads_environment_then_configuration(string? env, string? config, DataMode expected)
    {
        Assert.Equal(expected, DataModeGuard.Resolve(env, config));
    }

    [Fact]
    public void Resolve_rejects_unknown_values()
    {
        Assert.Throws<InvalidOperationException>(() => DataModeGuard.Resolve("production", null));
    }

    [Fact]
    public void Synthetic_mode_with_synthetic_providers_starts()
    {
        Assert.Empty(DataModeGuard.Problems(DataMode.Synthetic, new DemoModeOptions()));
    }

    [Fact]
    public void Real_mode_is_blocked_until_real_integrations_exist()
    {
        var problems = DataModeGuard.Problems(DataMode.Real, new DemoModeOptions());
        Assert.Single(problems);
        Assert.StartsWith(DataModeGuard.Blocked, problems[0]);
    }

    [Fact]
    public void Turning_off_a_synthetic_provider_without_a_real_one_is_refused()
    {
        var problems = DataModeGuard.Problems(DataMode.Synthetic, new DemoModeOptions { UseSyntheticAadhaar = false, UseSyntheticPassbook = false });
        Assert.Equal(2, problems.Count);
        Assert.All(problems, p => Assert.StartsWith(DataModeGuard.Blocked, p));
    }
}
