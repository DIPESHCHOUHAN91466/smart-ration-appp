using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.Extensions.Options;
using SmartRation.Api.Configuration;

namespace SmartRation.Api.Services.AI;

// Outcome of calling the optional Python AI service. Never throws for
// transport problems: an unavailable AI service is a normal, expected state.
public record PythonAiResult(bool Available, JsonElement? Data, string? ErrorCode, string? Message);

public interface IPythonAiClient
{
    bool IsConfigured { get; }

    Task<PythonAiResult> GetAsync(string path, IDictionary<string, string?> query, CancellationToken ct = default);

    Task<PythonAiResult> PostAsync(string path, object body, CancellationToken ct = default);

    Task<bool> IsHealthyAsync(CancellationToken ct = default);
}

public class PythonAiClient(HttpClient http, IOptions<AiServiceOptions> options, ILogger<PythonAiClient> logger) : IPythonAiClient
{
    private readonly AiServiceOptions _options = options.Value;

    public bool IsConfigured => !string.IsNullOrWhiteSpace(_options.BaseUrl) && !string.IsNullOrWhiteSpace(_options.ApiKey);

    public Task<PythonAiResult> GetAsync(string path, IDictionary<string, string?> query, CancellationToken ct = default)
    {
        var qs = string.Join("&", query
            .Where(kv => !string.IsNullOrEmpty(kv.Value))
            .Select(kv => $"{Uri.EscapeDataString(kv.Key)}={Uri.EscapeDataString(kv.Value!)}"));
        return SendAsync(HttpMethod.Get, qs.Length > 0 ? $"{path}?{qs}" : path, null, ct);
    }

    public Task<PythonAiResult> PostAsync(string path, object body, CancellationToken ct = default) =>
        SendAsync(HttpMethod.Post, path, JsonContent.Create(body), ct);

    private async Task<PythonAiResult> SendAsync(HttpMethod method, string url, HttpContent? content, CancellationToken ct)
    {
        if (!IsConfigured)
        {
            return new PythonAiResult(false, null, "AI_NOT_CONFIGURED", "The AI analytics service is not configured.");
        }

        var path = url.Split('?')[0];
        try
        {
            using var request = new HttpRequestMessage(method, url) { Content = content };
            request.Headers.Add("X-Api-Key", _options.ApiKey);
            using var response = await http.SendAsync(request, ct);

            JsonElement body;
            try
            {
                body = await response.Content.ReadFromJsonAsync<JsonElement>(cancellationToken: ct);
            }
            catch (JsonException)
            {
                // Proxy error page, truncated body, etc. — treat as malformed, not as data.
                logger.LogWarning("AI service {Path} returned a non-JSON body ({Status})", path, (int)response.StatusCode);
                return new PythonAiResult(false, null, "AI_MALFORMED_RESPONSE", "The AI service returned an unreadable response.");
            }

            if (response.IsSuccessStatusCode && body.ValueKind == JsonValueKind.Object && body.TryGetProperty("data", out var data))
            {
                return new PythonAiResult(true, data.Clone(), null, null);
            }

            var code = body.ValueKind == JsonValueKind.Object && body.TryGetProperty("error_code", out var c) ? c.GetString() : "AI_MALFORMED_RESPONSE";
            var message = body.ValueKind == JsonValueKind.Object && body.TryGetProperty("message", out var m) ? m.GetString() : "The AI service returned an unexpected response.";
            logger.LogWarning("AI service {Path} returned {Status} {Code}", path, (int)response.StatusCode, code);
            return new PythonAiResult(false, null, code, message);
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException or NotSupportedException)
        {
            logger.LogWarning("AI service {Path} unreachable: {Error}", path, ex.GetType().Name);
            return new PythonAiResult(false, null, "AI_UNAVAILABLE", "The AI analytics service is temporarily unavailable.");
        }
    }

    public async Task<bool> IsHealthyAsync(CancellationToken ct = default)
    {
        if (!IsConfigured)
        {
            return false;
        }

        try
        {
            using var response = await http.GetAsync("/health", ct);
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
        {
            return false;
        }
    }
}
