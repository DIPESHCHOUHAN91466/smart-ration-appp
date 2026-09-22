namespace SmartRation.Api.Models;

public enum VerificationAction
{
    QrScanned = 1,
    BeneficiaryVerified = 2,
    AadhaarStatusChecked = 3,
    PassbookStatusChecked = 4,
    OtpRequested = 5,
    OtpVerified = 6,
    OtpFailed = 7,
    CollectionConfirmed = 8,
    CollectionRejected = 9,
    TokenAlreadyUsed = 10
}

// Audit trail dedicated to the beneficiary-verification flow — separate
// from the general-purpose AuditLog already used elsewhere, since this one
// carries verification-specific fields and deliberately excludes sensitive
// personal data (no Aadhaar/mobile numbers, no OTP codes).
public class VerificationAuditLog
{
    public long Id { get; set; }

    public string? VerificationReference { get; set; }

    public string? TokenNumber { get; set; }

    public int? BeneficiaryId { get; set; }

    public int? ShopId { get; set; }

    public VerificationAction Action { get; set; }

    public string VerificationMethod { get; set; } = string.Empty; // QR / OTP

    public string Status { get; set; } = string.Empty; // SUCCESS / FAILED / BLOCKED

    public string? Reason { get; set; }

    public int? OperatorId { get; set; }

    public string? DeviceInfo { get; set; }

    public string? IpAddress { get; set; }

    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}
