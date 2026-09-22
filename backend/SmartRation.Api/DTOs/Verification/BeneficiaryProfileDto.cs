namespace SmartRation.Api.DTOs.Verification;

// The beneficiary's own verification profile view — no booking/token
// context, unlike BeneficiaryVerificationResponseDto which is scanned at a
// shop against a specific token.
public class BeneficiaryProfileDto
{
    public BeneficiarySummaryDto Beneficiary { get; set; } = null!;

    public FamilyDto Family { get; set; } = null!;

    public AadhaarVerificationDto AadhaarVerification { get; set; } = null!;

    public PassbookVerificationDto PassbookVerification { get; set; } = null!;

    public MobileVerificationDto MobileVerification { get; set; } = null!;
}
