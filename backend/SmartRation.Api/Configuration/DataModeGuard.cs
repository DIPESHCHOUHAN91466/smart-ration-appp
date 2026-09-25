namespace SmartRation.Api.Configuration;

// Which data the system runs on. The business services only ever see the interfaces
// (IAadhaarVerificationService, IPassbookVerificationService, ISmsProvider, ...); this mode
// decides which implementations are allowed behind them.
public enum DataMode
{
    Synthetic,
    Real,
}

// Validates the data mode at startup so the system can never silently mix synthetic and
// real data, or pretend a real integration exists when it doesn't.
public static class DataModeGuard
{
    public const string Blocked = "BLOCKED — REQUIRES EXTERNAL INTEGRATION";

    // DATA_MODE (environment) wins over the DataMode configuration key; default Synthetic.
    public static DataMode Resolve(string? environmentValue, string? configurationValue)
    {
        var raw = !string.IsNullOrWhiteSpace(environmentValue) ? environmentValue : configurationValue;
        if (string.IsNullOrWhiteSpace(raw))
        {
            return DataMode.Synthetic;
        }
        return Enum.TryParse<DataMode>(raw.Trim(), ignoreCase: true, out var mode)
            ? mode
            : throw new InvalidOperationException($"DATA_MODE must be 'synthetic' or 'real', not '{raw}'.");
    }

    // Returns the startup problems for this configuration (empty = OK to start).
    public static IReadOnlyList<string> Problems(DataMode mode, DemoModeOptions demo)
    {
        var problems = new List<string>();
        if (mode == DataMode.Real)
        {
            // No real provider exists yet. Real mode must wait for authorised integrations,
            // plus a separate database, consent, privacy and security review (data/real/README.md).
            problems.Add($"{Blocked}: DATA_MODE=real needs an authorised Aadhaar eKYC provider, a passbook/ration-card registry " +
                         "provider and a real SMS gateway. None is implemented yet — see data/real/README.md.");
            return problems;
        }
        if (!demo.UseSyntheticAadhaar)
        {
            problems.Add($"{Blocked}: Demo:UseSyntheticAadhaar=false, but no real Aadhaar verification provider is implemented.");
        }
        if (!demo.UseSyntheticPassbook)
        {
            problems.Add($"{Blocked}: Demo:UseSyntheticPassbook=false, but no real passbook verification provider is implemented.");
        }
        return problems;
    }
}
