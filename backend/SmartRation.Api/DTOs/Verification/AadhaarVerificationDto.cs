namespace SmartRation.Api.DTOs.Verification;

public class AadhaarVerificationDto
{
    public string Status { get; set; } = string.Empty; // NotVerified | Pending | Verified | Failed | Expired

    public string AadhaarMasked { get; set; } = string.Empty;

    public string? VerificationDate { get; set; }

    public string VerificationSource { get; set; } = string.Empty;

    public string VerificationMode { get; set; } = string.Empty;
}
