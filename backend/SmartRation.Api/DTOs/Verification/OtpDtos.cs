using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Verification;

public class OtpRequestRequestDto
{
    [Required, Phone]
    public string MobileNumber { get; set; } = string.Empty;
}

public class OtpRequestResponseDto
{
    public int OtpVerificationId { get; set; }

    public string MobileMasked { get; set; } = string.Empty;

    public int ExpiresInMinutes { get; set; }

    // Only populated when DemoOtpEnabled is true — a real provider never echoes the code.
    public string? DemoOtpValue { get; set; }
}

public class OtpVerifyRequestDto
{
    [Required]
    public int OtpVerificationId { get; set; }

    [Required, StringLength(6, MinimumLength = 6)]
    public string Code { get; set; } = string.Empty;
}
