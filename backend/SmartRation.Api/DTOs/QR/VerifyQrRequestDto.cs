using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Qr;

public class VerifyQrRequestDto
{
    [Required]
    public string QrCodeValue { get; set; } = string.Empty;
}
