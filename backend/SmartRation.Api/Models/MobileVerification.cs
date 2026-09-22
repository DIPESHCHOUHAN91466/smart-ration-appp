namespace SmartRation.Api.Models;

public enum MobileVerificationStatus
{
    NotVerified = 1,
    Pending = 2,
    Verified = 3,
    Failed = 4
}

public class MobileVerification
{
    public int Id { get; set; }

    public int BeneficiaryId { get; set; }

    public Beneficiary Beneficiary { get; set; } = null!;

    public string MobileMasked { get; set; } = string.Empty; // ******4821

    public MobileVerificationStatus Status { get; set; } = MobileVerificationStatus.NotVerified;

    public DateTime? VerifiedAt { get; set; }

    public string VerificationSource { get; set; } = "SYNTHETIC_DEMO";
}
