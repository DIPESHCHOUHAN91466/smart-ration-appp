using System.Security.Cryptography;
using System.Text;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Data;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

// DEMO/SYNTHETIC MODE — when Demo:DemoOtpEnabled is true, always issues the
// configured fixed demo code (never in production). Otherwise generates a
// random 6-digit code; either way only a hash is ever stored, matching the
// refresh-token pattern already used elsewhere in this codebase.
public class SyntheticOtpService(SmartRationDbContext db, IOptions<DemoModeOptions> options) : IOtpService
{
    private readonly DemoModeOptions _options = options.Value;

    public async Task<OtpVerification> RequestOtpAsync(int beneficiaryId, int requestedByUserId)
    {
        var beneficiary = await db.Beneficiaries.FirstOrDefaultAsync(b => b.Id == beneficiaryId)
            ?? throw new NotFoundException("Beneficiary not found.");

        if (!beneficiary.IsActive || beneficiary.IsBlocked)
        {
            throw new ForbiddenException("This beneficiary account is not active.");
        }

        var code = _options.DemoOtpEnabled
            ? _options.DemoOtpValue
            : RandomNumberGenerator.GetInt32(0, 1_000_000).ToString("D6");

        var record = new OtpVerification
        {
            BeneficiaryId = beneficiaryId,
            RequestedByUserId = requestedByUserId,
            OtpHash = HashCode(code),
            AttemptCount = 0,
            MaxAttempts = _options.OtpMaxAttempts,
            Status = OtpStatus.Pending,
            CreatedAt = DateTime.UtcNow,
            ExpiresAt = DateTime.UtcNow.AddMinutes(_options.OtpExpiryMinutes)
        };

        db.OtpVerifications.Add(record);
        await db.SaveChangesAsync();
        return record;
    }

    public async Task<OtpVerification> VerifyOtpAsync(int otpVerificationId, string code)
    {
        var record = await db.OtpVerifications.FirstOrDefaultAsync(o => o.Id == otpVerificationId)
            ?? throw new NotFoundException("OTP request not found.");

        if (record.Status != OtpStatus.Pending)
        {
            throw new BadRequestException($"This OTP request is already {record.Status}.");
        }

        if (DateTime.UtcNow > record.ExpiresAt)
        {
            record.Status = OtpStatus.Expired;
            await db.SaveChangesAsync();
            throw new BadRequestException("OTP has expired. Please request a new one.");
        }

        if (record.AttemptCount >= record.MaxAttempts)
        {
            record.Status = OtpStatus.Failed;
            await db.SaveChangesAsync();
            throw new BadRequestException("Maximum OTP attempts exceeded. Please request a new one.");
        }

        if (!string.Equals(HashCode(code), record.OtpHash, StringComparison.Ordinal))
        {
            record.AttemptCount += 1;
            if (record.AttemptCount >= record.MaxAttempts)
            {
                record.Status = OtpStatus.Failed;
            }
            await db.SaveChangesAsync();
            throw new BadRequestException($"Incorrect OTP. {Math.Max(0, record.MaxAttempts - record.AttemptCount)} attempt(s) remaining.");
        }

        record.Status = OtpStatus.Verified;
        record.VerifiedAt = DateTime.UtcNow;
        await db.SaveChangesAsync();
        return record;
    }

    private static string HashCode(string code) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(code)));
}
