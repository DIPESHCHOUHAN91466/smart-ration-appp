using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Qr;

namespace SmartRation.Api.Services;

public class QrService(
    SmartRationDbContext db,
    IOptions<QrOptions> options,
    ICurrentUserService currentUser) : IQrService
{
    private readonly QrOptions _options = options.Value;

    public string ComputeQrValue(int tokenId, string tokenNumber)
    {
        var payload = $"{tokenId}:{tokenNumber}";
        var signatureBytes = HMACSHA256.HashData(Encoding.UTF8.GetBytes(_options.Secret), Encoding.UTF8.GetBytes(payload));
        var signature = Convert.ToHexString(signatureBytes)[..16];
        return $"SRQR-{tokenId}-{signature}";
    }

    public async Task<string> RegenerateForTokenAsync(int tokenId)
    {
        var token = await db.Tokens.FirstOrDefaultAsync(t => t.Id == tokenId)
            ?? throw new NotFoundException("Token not found.");

        if (token.UserId != currentUser.UserId && currentUser.Role is not (UserRole.Admin or UserRole.GovernmentOfficial))
        {
            throw new ForbiddenException("You can only generate a QR code for your own token.");
        }

        if (token.Status is TokenStatus.Completed or TokenStatus.Cancelled)
        {
            throw new BadRequestException($"Cannot generate a QR code for a token in {token.Status} status.");
        }

        token.QRCodeValue = ComputeQrValue(token.Id, token.TokenNumber);
        await db.SaveChangesAsync();

        return token.QRCodeValue;
    }

    public async Task<TokenDto> VerifyAsync(string qrValue)
    {
        var token = await ResolveTokenForVerificationAsync(qrValue);

        if (token.Status == TokenStatus.Completed)
        {
            throw new ConflictException("This QR code has already been used for collection.");
        }

        if (token.Status == TokenStatus.Cancelled)
        {
            throw new ConflictException("This booking was cancelled.");
        }

        return token.ToDto();
    }

    public async Task<Token> ResolveTokenForVerificationAsync(string qrValue)
    {
        var parsed = ParseScannedQr(qrValue);
        var token = await ResolveReferenceAsync(parsed.Reference);

        // The envelope is signed, so a mismatch here means the signed
        // reference and token number were issued for different bookings.
        if (parsed.ClaimedTokenNumber is not null &&
            !string.Equals(parsed.ClaimedTokenNumber, token.TokenNumber, StringComparison.Ordinal))
        {
            throw new BadRequestException("QR code signature is invalid.") { ErrorCode = QrScanStatus.InvalidSignature };
        }

        return token;
    }

    public string BuildSignedPayload(Token token)
    {
        // Seeded showcase tokens keep their fixed SRQR-DEMO alias; everything
        // else gets the freshly derived signed reference.
        var reference = token.QRCodeValue?.StartsWith("SRQR-DEMO-", StringComparison.Ordinal) == true
            ? token.QRCodeValue
            : ComputeQrValue(token.Id, token.TokenNumber);
        var issuedAt = FormatUtc(token.CreatedAt);

        // Valid until the end of the booked collection day — the same window the
        // server-side verification summary enforces ("collection date has passed").
        var expiresAt = FormatUtc(token.TimeSlot.SlotDate.Date.AddDays(1));

        var envelope = new Dictionary<string, string>
        {
            ["version"] = QrPayloadContract.Version,
            ["project"] = QrPayloadContract.Project,
            ["type"] = QrPayloadContract.Type,
            ["reference"] = reference,
            ["token"] = token.TokenNumber,
            ["issuedAt"] = issuedAt,
            ["expiresAt"] = expiresAt
        };
        envelope["signature"] = SignEnvelope(envelope);

        return JsonSerializer.Serialize(envelope);
    }

    public async Task<string> GetPayloadForTokenAsync(int tokenId)
    {
        var token = await TokenQuery().FirstOrDefaultAsync(t => t.Id == tokenId)
            ?? throw new NotFoundException("Token not found.");

        if (token.UserId != currentUser.UserId && currentUser.Role is not (UserRole.Admin or UserRole.GovernmentOfficial))
        {
            throw new ForbiddenException("You can only view the QR code for your own token.");
        }

        return BuildSignedPayload(token);
    }

    public ParsedQr ParseScannedQr(string rawQr)
    {
        var raw = (rawQr ?? string.Empty).Trim();
        if (raw.Length == 0 || raw.Length > 2048)
        {
            throw new BadRequestException("QR code is not recognized.") { ErrorCode = QrScanStatus.InvalidFormat };
        }

        // Bare reference: typed manually, or a QR printed before the envelope existed.
        if (!raw.StartsWith('{') && !raw.StartsWith('['))
        {
            if (!raw.StartsWith("SRQR-", StringComparison.Ordinal))
            {
                throw new BadRequestException("This QR code does not belong to the Smart Ration system.") { ErrorCode = QrScanStatus.InvalidProject };
            }
            return new ParsedQr(raw, null);
        }

        Dictionary<string, string> fields;
        try
        {
            using var doc = JsonDocument.Parse(raw);
            if (doc.RootElement.ValueKind != JsonValueKind.Object)
            {
                throw new JsonException();
            }
            fields = doc.RootElement.EnumerateObject()
                .Where(p => p.Value.ValueKind == JsonValueKind.String)
                .ToDictionary(p => p.Name, p => p.Value.GetString()!);
        }
        catch (JsonException)
        {
            throw new BadRequestException("QR code is malformed.") { ErrorCode = QrScanStatus.InvalidFormat };
        }

        // Project/type first so an unrelated JSON QR gets the clearest message.
        if (fields.GetValueOrDefault("project") != QrPayloadContract.Project)
        {
            throw new BadRequestException("This QR code does not belong to the Smart Ration system.") { ErrorCode = QrScanStatus.InvalidProject };
        }

        if (QrPayloadContract.RequiredFields.Any(f => string.IsNullOrWhiteSpace(fields.GetValueOrDefault(f))))
        {
            throw new BadRequestException("Required QR information is missing.") { ErrorCode = QrScanStatus.MissingFields };
        }

        if (fields["type"] != QrPayloadContract.Type)
        {
            throw new BadRequestException("This QR code is not a ration token.") { ErrorCode = QrScanStatus.InvalidType };
        }

        if (fields["version"] != QrPayloadContract.Version)
        {
            throw new BadRequestException("This QR code version is not supported.") { ErrorCode = QrScanStatus.UnsupportedVersion };
        }

        // Constant-time compare so the signature can't be probed byte by byte.
        var expected = Encoding.ASCII.GetBytes(SignEnvelope(fields));
        var actual = Encoding.ASCII.GetBytes(fields["signature"].ToUpperInvariant());
        if (!CryptographicOperations.FixedTimeEquals(expected, actual))
        {
            throw new BadRequestException("QR code signature is invalid.") { ErrorCode = QrScanStatus.InvalidSignature };
        }

        // Expiry is only trusted after the signature check proves the server issued it.
        if (!DateTime.TryParse(fields["expiresAt"], CultureInfo.InvariantCulture, DateTimeStyles.AdjustToUniversal | DateTimeStyles.AssumeUniversal, out var expiresAt))
        {
            throw new BadRequestException("QR code is malformed.") { ErrorCode = QrScanStatus.InvalidFormat };
        }
        if (DateTime.UtcNow > expiresAt)
        {
            throw new BadRequestException("This collection QR code is no longer valid.") { ErrorCode = QrScanStatus.Expired };
        }

        return new ParsedQr(fields["reference"], fields["token"]);
    }

    // HMAC over a fixed field order. The "envelope:" prefix keeps these
    // signatures from ever colliding with the SRQR reference signatures that
    // share the same secret.
    private string SignEnvelope(IReadOnlyDictionary<string, string> fields)
    {
        var canonical = "envelope:" + string.Join("|",
            fields["version"], fields["project"], fields["type"], fields["reference"],
            fields["token"], fields["issuedAt"], fields["expiresAt"]);

        var bytes = HMACSHA256.HashData(Encoding.UTF8.GetBytes(_options.Secret), Encoding.UTF8.GetBytes(canonical));

        // Truncated to 128 bits: still infeasible to forge, and keeps the QR
        // image sparse enough to scan reliably from a phone screen.
        return Convert.ToHexString(bytes)[..32];
    }

    private static string FormatUtc(DateTime value) =>
        DateTime.SpecifyKind(value, DateTimeKind.Utc).ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);

    private async Task<Token> ResolveReferenceAsync(string qrValue)
    {
        var parts = qrValue.Split('-');
        Token? token;

        if (parts.Length == 3 && parts[0] == "SRQR" && int.TryParse(parts[1], out var tokenId))
        {
            // Standard signed reference: SRQR-{tokenId}-{hmacSignature}.
            token = await TokenQuery().FirstOrDefaultAsync(t => t.Id == tokenId)
                ?? throw new NotFoundException("QR code does not match any booking.") { ErrorCode = QrScanStatus.TokenNotFound };

            var expected = ComputeQrValue(token.Id, token.TokenNumber);
            if (!string.Equals(expected, qrValue, StringComparison.Ordinal))
            {
                throw new BadRequestException("QR code signature is invalid.") { ErrorCode = QrScanStatus.InvalidSignature };
            }
        }
        else if (qrValue.StartsWith("SRQR-DEMO-", StringComparison.Ordinal))
        {
            // The /qr-demo showcase page uses a handful of fixed, human-readable
            // aliases (SRQR-DEMO-001 etc.) seeded directly onto specific demo
            // tokens — an exact-match lookup, never a general bypass of the
            // signature check above.
            token = await TokenQuery().FirstOrDefaultAsync(t => t.QRCodeValue == qrValue)
                ?? throw new NotFoundException("QR code does not match any booking.") { ErrorCode = QrScanStatus.TokenNotFound };
        }
        else
        {
            throw new BadRequestException("QR code is not recognized.") { ErrorCode = QrScanStatus.InvalidFormat };
        }

        if (currentUser.Role == UserRole.ShopOwner && token.RationShopId != currentUser.RationShopId)
        {
            throw new ForbiddenException("This token belongs to another ration shop.") { ErrorCode = QrScanStatus.WrongShop };
        }

        return token;
    }

    private IQueryable<Token> TokenQuery() =>
        db.Tokens
            .Include(t => t.User)
            .Include(t => t.RationShop)
            .Include(t => t.TimeSlot)
            .Include(t => t.Items);
}
