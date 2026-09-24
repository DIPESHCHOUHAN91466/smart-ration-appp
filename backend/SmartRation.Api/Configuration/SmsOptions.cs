namespace SmartRation.Api.Configuration;

public class SmsOptions
{
    public const string SectionName = "Sms";

    // "Mock" (development: sends nothing) or "Http" (real gateway).
    // Outside Development the app refuses to start with Mock.
    public string Provider { get; set; } = "Mock";

    // Http provider only. Set via user-secrets / Sms__ApiKey — never committed.
    public string BaseUrl { get; set; } = string.Empty;

    public string ApiKey { get; set; } = string.Empty;

    public string SenderId { get; set; } = "SMRTRN";
}
