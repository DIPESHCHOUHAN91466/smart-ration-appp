using System.Text.Json;

namespace SmartRation.Api.DTOs.AI;

// Envelope for Python-backed analytics. The request itself always succeeds
// (HTTP 200) so the UI can render a clear "AI unavailable" state instead of
// an error page — the core PDS never depends on this data.
public class AiAnalyticsResponseDto
{
    public bool Available { get; set; }

    // "python-ai" (live analytics), "fallback" (built-in C# rules) or "unavailable".
    public string Source { get; set; } = "unavailable";

    public JsonElement? Data { get; set; }

    // Built-in rule-based result when the Python service is down (forecast/queue only).
    public object? Fallback { get; set; }

    public string? ErrorCode { get; set; }

    public string? Message { get; set; }
}
