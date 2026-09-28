namespace SmartRation.Api.Configuration;

// The optional Python AI analytics service (ai).
public class AiServiceOptions
{
    public const string SectionName = "AiService";

    // Empty BaseUrl disables the integration entirely (endpoints report "unavailable").
    public string BaseUrl { get; set; } = string.Empty;

    // Shared secret sent as X-Api-Key. Set via user-secrets / AiService__ApiKey.
    public string ApiKey { get; set; } = string.Empty;

    // Kept short: an optional analytics call must never hold up a request for long.
    public int TimeoutSeconds { get; set; } = 8;
}
