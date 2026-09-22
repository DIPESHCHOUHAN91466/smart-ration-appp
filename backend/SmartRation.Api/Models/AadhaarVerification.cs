namespace SmartRation.Api.Models;

// NotVerified/Pending/Verified/Failed/Expired — mirrors what a real Aadhaar
// eKYC provider would report. This system never performs live biometric
// verification; it only reads (and, in synthetic mode, seeds) this status.
public enum AadhaarVerificationStatus
{
    NotVerified = 1,
    Pending = 2,
    Verified = 3,
    Failed = 4,
    Expired = 5
}

public class AadhaarVerification
{
    public int Id { get; set; }

    public int BeneficiaryId { get; set; }

    public Beneficiary Beneficiary { get; set; } = null!;

    // Synthetic reference only — never a real Aadhaar number. AAD-DEMO-000001
    public string AadhaarReferenceId { get; set; } = string.Empty;

    // Masked display value only, e.g. XXXX-XXXX-4821. The full number is
    // never generated or stored anywhere in this system.
    public string AadhaarMasked { get; set; } = string.Empty;

    public AadhaarVerificationStatus Status { get; set; } = AadhaarVerificationStatus.NotVerified;

    public DateTime? VerificationDate { get; set; }

    // SYNTHETIC_DEMO until an authorized provider replaces SyntheticAadhaarVerificationService.
    public string VerificationSource { get; set; } = "SYNTHETIC_DEMO";

    // PRE_VERIFIED for demo data seeded already-verified; a real provider
    // would report LIVE_EKYC or similar.
    public string VerificationMode { get; set; } = "PRE_VERIFIED";
}
