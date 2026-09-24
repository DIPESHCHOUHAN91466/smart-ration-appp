using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Auth;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Services;

public class AuthService(
    SmartRationDbContext db,
    IJwtService jwtService,
    IAuditLogService auditLog,
    IBeneficiaryProvisioningService beneficiaryProvisioning,
    ILogger<AuthService> logger) : IAuthService
{
    public async Task<AuthResponseDto> RegisterAsync(RegisterRequestDto request)
    {
        var normalizedEmail = request.Email.Trim().ToLowerInvariant();

        var emailTaken = await db.Users.AnyAsync(u => u.Email == normalizedEmail);
        if (emailTaken)
        {
            throw new ConflictException("An account with this email already exists.");
        }

        var mobileTaken = await db.Users.AnyAsync(u => u.MobileNumber == request.MobileNumber);
        if (mobileTaken)
        {
            throw new ConflictException("An account with this mobile number already exists.");
        }

        var user = new User
        {
            FullName = request.FullName.Trim(),
            Email = normalizedEmail,
            MobileNumber = request.MobileNumber.Trim(),
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password),
            Role = UserRole.RuralUser,
            IsActive = true
        };

        db.Users.Add(user);
        await db.SaveChangesAsync();

        var beneficiary = await beneficiaryProvisioning.ProvisionAsync(user);

        logger.LogInformation("New user registered: {UserId} ({Email}), beneficiary {BeneficiaryCode}", user.Id, user.Email, beneficiary.BeneficiaryCode);
        await auditLog.LogAsync(user.Id, "REGISTER", nameof(User), user.Id.ToString());

        return await IssueTokensAsync(user);
    }

    public async Task<AuthResponseDto> LoginAsync(LoginRequestDto request)
    {
        var normalizedEmail = request.Email.Trim().ToLowerInvariant();
        var user = await db.Users.FirstOrDefaultAsync(u => u.Email == normalizedEmail);

        if (user is null || !BCrypt.Net.BCrypt.Verify(request.Password, user.PasswordHash))
        {
            await auditLog.LogAsync(user?.Id, "LOGIN_FAILED", nameof(User), details: $"email={MaskEmail(normalizedEmail)}", result: "FAILED");
            throw new UnauthorizedApiException("Invalid email or password.");
        }

        if (!user.IsActive)
        {
            throw new ForbiddenException("This account has been deactivated. Contact your ration shop or district office.");
        }

        logger.LogInformation("User logged in: {UserId} ({Role})", user.Id, user.Role);
        await auditLog.LogAsync(user.Id, "LOGIN", nameof(User), user.Id.ToString(), role: user.Role.ToString());

        return await IssueTokensAsync(user);
    }

    public async Task<AuthResponseDto> RefreshAsync(string rawRefreshToken)
    {
        var tokenHash = jwtService.HashToken(rawRefreshToken);

        var existing = await db.RefreshTokens
            .Include(rt => rt.User)
            .FirstOrDefaultAsync(rt => rt.TokenHash == tokenHash);

        if (existing is null || !existing.IsActive)
        {
            throw new UnauthorizedApiException("Refresh token is invalid or has expired. Please log in again.");
        }

        var (rawNewToken, newHash, expiresAt) = jwtService.GenerateRefreshToken();

        existing.RevokedAt = DateTime.UtcNow;
        existing.ReplacedByTokenHash = newHash;

        db.RefreshTokens.Add(new RefreshToken
        {
            UserId = existing.UserId,
            TokenHash = newHash,
            ExpiresAt = expiresAt
        });

        await db.SaveChangesAsync();

        var (accessToken, accessExpiresAt) = jwtService.GenerateAccessToken(existing.User);

        return new AuthResponseDto
        {
            AccessToken = accessToken,
            RefreshToken = rawNewToken,
            AccessTokenExpiresAt = accessExpiresAt,
            User = existing.User.ToSummaryDto()
        };
    }

    public async Task LogoutAsync(string rawRefreshToken)
    {
        var tokenHash = jwtService.HashToken(rawRefreshToken);
        var existing = await db.RefreshTokens.FirstOrDefaultAsync(rt => rt.TokenHash == tokenHash);

        if (existing is not null && existing.RevokedAt is null)
        {
            existing.RevokedAt = DateTime.UtcNow;
            await db.SaveChangesAsync();
            await auditLog.LogAsync(existing.UserId, "LOGOUT", nameof(User), existing.UserId.ToString());
        }
    }

    private async Task<AuthResponseDto> IssueTokensAsync(User user)
    {
        var (accessToken, accessExpiresAt) = jwtService.GenerateAccessToken(user);
        var (rawRefreshToken, refreshHash, refreshExpiresAt) = jwtService.GenerateRefreshToken();

        db.RefreshTokens.Add(new RefreshToken
        {
            UserId = user.Id,
            TokenHash = refreshHash,
            ExpiresAt = refreshExpiresAt
        });

        await db.SaveChangesAsync();

        return new AuthResponseDto
        {
            AccessToken = accessToken,
            RefreshToken = rawRefreshToken,
            AccessTokenExpiresAt = accessExpiresAt,
            User = user.ToSummaryDto()
        };
    }

    // "rahul@example.com" -> "r***@example.com"
    private static string MaskEmail(string email)
    {
        var at = email.IndexOf('@');
        return at <= 0 ? "***" : $"{email[0]}***{email[at..]}";
    }
}
