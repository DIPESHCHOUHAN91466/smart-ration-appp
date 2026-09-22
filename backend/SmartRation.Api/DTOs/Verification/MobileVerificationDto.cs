namespace SmartRation.Api.DTOs.Verification;

public class MobileVerificationDto
{
    public string MobileMasked { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty; // NotVerified | Pending | Verified | Failed

    public string? VerifiedAt { get; set; }
}
