using System.ComponentModel.DataAnnotations;
using SmartRation.Api.DTOs.Verification;

namespace SmartRation.Api.DTOs.Qr;

public class QrScanRequestDto
{
    // Raw text decoded from the QR image (signed JSON envelope) or a manually
    // typed SRQR reference. Both go through the same validation pipeline.
    [Required]
    [MaxLength(2048)]
    public string QrData { get; set; } = string.Empty;
}

public class QrScanResultDto
{
    // True only when the QR is authentic AND the booking is ready for collection.
    public bool Verified { get; set; }

    // One of QrScanStatus (VERIFIED, EXPIRED, WRONG_SHOP, ...).
    public string Status { get; set; } = string.Empty;

    public string Message { get; set; } = string.Empty;

    public string? TokenNumber { get; set; }

    // Full beneficiary/booking/entitlement view — present whenever the QR
    // resolved to a booking at this shop (including blocked ones, so the
    // operator can see why), null for invalid/unrecognized QR codes.
    public BeneficiaryVerificationResponseDto? Verification { get; set; }
}
