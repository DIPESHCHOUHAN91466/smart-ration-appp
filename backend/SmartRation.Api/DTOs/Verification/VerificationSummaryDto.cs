namespace SmartRation.Api.DTOs.Verification;

public class VerificationSummaryDto
{
    public bool AadhaarVerified { get; set; }

    public bool PassbookVerified { get; set; }

    public bool MobileVerified { get; set; }

    public bool TokenValid { get; set; }

    public bool FamilyEligible { get; set; }

    public bool EntitlementAvailable { get; set; }

    // READY_FOR_RATION_COLLECTION | COLLECTION_BLOCKED
    public string OverallStatus { get; set; } = string.Empty;

    // Populated only when OverallStatus is COLLECTION_BLOCKED.
    public string? BlockedReason { get; set; }
}
