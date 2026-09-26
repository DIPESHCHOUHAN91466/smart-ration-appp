namespace SmartRation.Api.Configuration;

// Startup rules for any environment other than Development: never a fixed demo OTP, and never an SMS
// provider that silently sends nothing — except a public demo on SYNTHETIC data that explicitly opts in
// with Sms:AllowMockOutsideDevelopment=true (it then logs a warning at startup).
public static class ProductionGuard
{
    public static IReadOnlyList<string> Problems(bool isDevelopment, DataMode mode, DemoModeOptions demo, SmsOptions sms)
    {
        var problems = new List<string>();
        if (isDevelopment)
        {
            return problems;
        }
        if (demo.DemoOtpEnabled)
        {
            problems.Add("Demo:DemoOtpEnabled must be false outside Development (set Demo__DemoOtpEnabled=false).");
        }
        if (!string.Equals(sms.Provider, "Http", StringComparison.OrdinalIgnoreCase) && !UsesSyntheticDemoSms(isDevelopment, mode, sms))
        {
            problems.Add("Sms:Provider must be 'Http' (a real gateway) outside Development. A synthetic-data demo may set " +
                         "Sms__AllowMockOutsideDevelopment=true instead; that is never allowed with DATA_MODE=real.");
        }
        return problems;
    }

    // True when a non-Development deployment runs the mock SMS provider under the synthetic-demo opt-in.
    public static bool UsesSyntheticDemoSms(bool isDevelopment, DataMode mode, SmsOptions sms) =>
        !isDevelopment
        && !string.Equals(sms.Provider, "Http", StringComparison.OrdinalIgnoreCase)
        && sms.AllowMockOutsideDevelopment
        && mode == DataMode.Synthetic;
}
