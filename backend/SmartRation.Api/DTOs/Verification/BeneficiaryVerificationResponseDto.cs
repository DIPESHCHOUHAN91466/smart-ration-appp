namespace SmartRation.Api.DTOs.Verification;

// The single consolidated payload the shopkeeper's verification screen
// renders — everything needed to make the collection decision in one call.
public class BeneficiaryVerificationResponseDto
{
    public BeneficiarySummaryDto Beneficiary { get; set; } = null!;

    public FamilyDto Family { get; set; } = null!;

    public AadhaarVerificationDto AadhaarVerification { get; set; } = null!;

    public PassbookVerificationDto PassbookVerification { get; set; } = null!;

    public MobileVerificationDto MobileVerification { get; set; } = null!;

    public BookingSummaryDto Booking { get; set; } = null!;

    public EntitlementSummaryDto Entitlement { get; set; } = null!;

    public List<CollectionHistoryItemDto> PreviousCollections { get; set; } = [];

    public VerificationSummaryDto VerificationSummary { get; set; } = null!;
}
