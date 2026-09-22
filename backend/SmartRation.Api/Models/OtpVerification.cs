namespace SmartRation.Api.Models;

public enum OtpStatus
{
    Pending = 1,
    Verified = 2,
    Expired = 3,
    Failed = 4
}

// The OTP fallback path used when a beneficiary's QR can't be scanned.
// This is an identity/token-recovery mechanism only — it never claims to
// be Aadhaar biometric verification.
public class OtpVerification
{
    public int Id { get; set; }

    public int BeneficiaryId { get; set; }

    public Beneficiary Beneficiary { get; set; } = null!;

    public int RequestedByUserId { get; set; }

    // Never the raw OTP — only a hash, same pattern as refresh tokens.
    public string OtpHash { get; set; } = string.Empty;

    public int AttemptCount { get; set; } = 0;

    public int MaxAttempts { get; set; } = 3;

    public OtpStatus Status { get; set; } = OtpStatus.Pending;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime ExpiresAt { get; set; }

    public DateTime? VerifiedAt { get; set; }
}
