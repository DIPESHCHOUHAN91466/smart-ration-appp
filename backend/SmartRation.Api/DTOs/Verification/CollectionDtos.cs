using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Verification;

public class ConfirmCollectionRequestDto
{
    [Required]
    public int TokenId { get; set; }

    // QR or OTP — which path verified this beneficiary before confirming.
    [Required]
    public string VerificationMethod { get; set; } = "QR";
}

public class CollectionReceiptDto
{
    public string CollectionCode { get; set; } = string.Empty;

    public string TokenNumber { get; set; } = string.Empty;

    public string BeneficiaryName { get; set; } = string.Empty;

    public int FamilySize { get; set; }

    public string SchemeCode { get; set; } = string.Empty;

    public List<CollectedItemDto> IssuedItems { get; set; } = [];

    public decimal TotalQuantityKg { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public string CollectedAt { get; set; } = string.Empty;
}
