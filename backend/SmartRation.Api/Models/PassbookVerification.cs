namespace SmartRation.Api.Models;

public enum PassbookVerificationStatus
{
    NotVerified = 1,
    Pending = 2,
    Verified = 3,
    Failed = 4
}

public class PassbookVerification
{
    public int Id { get; set; }

    public int BeneficiaryId { get; set; }

    public Beneficiary Beneficiary { get; set; } = null!;

    public string PassbookNumber { get; set; } = string.Empty; // PB-DEMO-0001

    // Record status of the passbook itself (ACTIVE / INACTIVE), distinct
    // from whether it has been verified.
    public string Status { get; set; } = "ACTIVE";

    public PassbookVerificationStatus VerificationStatus { get; set; } = PassbookVerificationStatus.NotVerified;

    public DateTime LastUpdated { get; set; } = DateTime.UtcNow;

    public string VerificationSource { get; set; } = "SYNTHETIC_DEMO";
}
