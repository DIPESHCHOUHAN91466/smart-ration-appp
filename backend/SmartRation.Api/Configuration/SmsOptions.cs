namespace SmartRation.Api.Configuration;

public class SmsOptions
{
    public const string SectionName = "Sms";

    // "Mock" (development: sends nothing) or "Http" (real gateway).
    // Outside Development the app refuses to start with Mock (see ProductionGuard) ...
    public string Provider { get; set; } = "Mock";

    // ... unless this is true AND DATA_MODE=synthetic: a public demo on synthetic data, where no real
    // person should receive an SMS anyway. Never allowed with real data.
    public bool AllowMockOutsideDevelopment { get; set; }

    // Http provider only. Set via user-secrets / Sms__ApiKey — never committed.
    public string BaseUrl { get; set; } = string.Empty;

    public string ApiKey { get; set; } = string.Empty;

    public string SenderId { get; set; } = "SMRTRN";
}
