namespace SmartRation.Api.DTOs.Verification;

public class PassbookVerificationDto
{
    public string PassbookNumber { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty; // ACTIVE | INACTIVE

    public string VerificationStatus { get; set; } = string.Empty; // NotVerified | Pending | Verified | Failed

    public string LastUpdated { get; set; } = string.Empty;

    public string VerificationSource { get; set; } = string.Empty;
}
