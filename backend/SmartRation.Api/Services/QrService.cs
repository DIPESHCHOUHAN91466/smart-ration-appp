using System.Security.Cryptography;
using System.Text;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;

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
        var parts = qrValue.Split('-');
        if (parts.Length != 3 || parts[0] != "SRQR" || !int.TryParse(parts[1], out var tokenId))
        {
            throw new BadRequestException("QR code is not recognized.");
        }

        var token = await db.Tokens
            .Include(t => t.User)
            .Include(t => t.RationShop)
            .Include(t => t.TimeSlot)
            .Include(t => t.Items)
            .FirstOrDefaultAsync(t => t.Id == tokenId)
            ?? throw new NotFoundException("QR code does not match any booking.");

        var expected = ComputeQrValue(token.Id, token.TokenNumber);
        if (!string.Equals(expected, qrValue, StringComparison.Ordinal))
        {
            throw new BadRequestException("QR code signature is invalid.");
        }

        if (currentUser.Role == UserRole.ShopOwner && token.RationShopId != currentUser.RationShopId)
        {
            throw new ForbiddenException("This booking belongs to a different ration shop.");
        }

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
}
