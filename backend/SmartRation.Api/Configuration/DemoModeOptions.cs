namespace SmartRation.Api.Configuration;

// Toggles for the synthetic/demo verification providers. Flipping these to
// false is what future real integrations hook into — see
// Services/Verification/I*.cs for the abstractions each flag gates.
public class DemoModeOptions
{
    public const string SectionName = "Demo";

    public bool DemoMode { get; set; } = true;

    public bool DemoOtpEnabled { get; set; } = true;

    public string DemoOtpValue { get; set; } = "123456";

    public bool UseSyntheticAadhaar { get; set; } = true;

    public bool UseSyntheticPassbook { get; set; } = true;

    public bool UseSyntheticMapData { get; set; } = true;

    public int OtpExpiryMinutes { get; set; } = 5;

    public int OtpMaxAttempts { get; set; } = 3;
}
