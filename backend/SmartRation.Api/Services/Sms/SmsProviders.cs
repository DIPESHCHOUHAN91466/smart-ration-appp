using System.Net.Http.Json;
using Microsoft.Extensions.Options;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;

namespace SmartRation.Api.Services.Sms;

public record SmsSendResult(bool Sent, string Provider, string? ProviderMessageId = null, string? Error = null);

public interface ISmsProvider
{
    string Name { get; }

    Task<SmsSendResult> SendAsync(string phone, string message, CancellationToken ct = default);
}

// DEVELOPMENT IMPLEMENTATION. Sends nothing. Logs only the masked number and
// message length — never the message itself, because it contains the OTP.
public class MockSmsProvider(ILogger<MockSmsProvider> logger) : ISmsProvider
{
    public string Name => "Mock";

    public Task<SmsSendResult> SendAsync(string phone, string message, CancellationToken ct = default)
    {
        logger.LogInformation("[MOCK SMS] Not sent. To {Phone}, {Length} chars.", MaskingUtil.MaskMobile(phone), message.Length);
        return Task.FromResult(new SmsSendResult(true, Name, $"mock-{Guid.NewGuid():N}"));
    }
}

// PRODUCTION INTEGRATION REQUIRED. Generic JSON-over-HTTPS gateway adapter:
// POST {BaseUrl} with { to, sender, message } and a bearer API key. Real
// providers (MSG91, Gupshup, Twilio, NIC SMS gateway...) differ in payload —
// adapt this class to the chosen provider's contract and DLT template rules.
// Credentials come only from configuration (user-secrets / environment).
public class HttpSmsProvider(HttpClient http, IOptions<SmsOptions> options, ILogger<HttpSmsProvider> logger) : ISmsProvider
{
    private readonly SmsOptions _options = options.Value;

    public string Name => "Http";

    public async Task<SmsSendResult> SendAsync(string phone, string message, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(_options.BaseUrl) || string.IsNullOrWhiteSpace(_options.ApiKey))
        {
            return new SmsSendResult(false, Name, Error: "SMS gateway is not configured.");
        }

        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, _options.BaseUrl)
            {
                Content = JsonContent.Create(new { to = phone, sender = _options.SenderId, message })
            };
            request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", _options.ApiKey);

            using var response = await http.SendAsync(request, ct);
            if (!response.IsSuccessStatusCode)
            {
                logger.LogWarning("SMS gateway returned {Status} for {Phone}", (int)response.StatusCode, MaskingUtil.MaskMobile(phone));
                return new SmsSendResult(false, Name, Error: $"Gateway returned {(int)response.StatusCode}.");
            }
            return new SmsSendResult(true, Name);
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException)
        {
            logger.LogWarning("SMS gateway unreachable for {Phone}: {Error}", MaskingUtil.MaskMobile(phone), ex.GetType().Name);
            return new SmsSendResult(false, Name, Error: "SMS gateway unreachable.");
        }
    }
}
