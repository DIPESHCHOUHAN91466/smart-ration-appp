namespace SmartRation.Api.Configuration;

public class QrOptions
{
    public const string SectionName = "Qr";

    // HMAC signing secret for QR payloads. Never the same value as Jwt:Key.
    public string Secret { get; set; } = string.Empty;
}
