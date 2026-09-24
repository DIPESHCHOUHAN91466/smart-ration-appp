using SmartRation.Api.DTOs.AI;

namespace SmartRation.Api.DTOs.Verification;

public class BeneficiaryProfileDetailsDto
{
    public int Id { get; set; }

    public string BeneficiaryCode { get; set; } = string.Empty;

    public string FullName { get; set; } = string.Empty;

    public string Gender { get; set; } = string.Empty;

    public string? DateOfBirth { get; set; }

    public string MobileMasked { get; set; } = string.Empty;

    public string Village { get; set; } = string.Empty;

    public string District { get; set; } = string.Empty;

    public string State { get; set; } = string.Empty;

    public string Pincode { get; set; } = string.Empty;

    public string? ProfilePhotoUrl { get; set; }

    public bool IsActive { get; set; }

    public bool IsBlocked { get; set; }

    public string RegistrationDate { get; set; } = string.Empty;

    public string? LastCollectionDate { get; set; }

    public string? NextCollectionDate { get; set; }
}

public class RationCardDto
{
    public string RationCardNumber { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public string SchemeCode { get; set; } = string.Empty;

    public string SchemeName { get; set; } = string.Empty;

    public int FamilySize { get; set; }
}

public class CurrentQrInfoDto
{
    public int TokenId { get; set; }

    public string TokenNumber { get; set; } = string.Empty;

    public string? QrCodeValue { get; set; }

    public string Status { get; set; } = string.Empty;

    public string CollectionDate { get; set; } = string.Empty;

    public string BookingTime { get; set; } = string.Empty;

    public string ShopName { get; set; } = string.Empty;
}

public class BeneficiaryFullProfileDto
{
    public BeneficiaryProfileDetailsDto Profile { get; set; } = null!;

    public FamilyDto Family { get; set; } = null!;

    public RationCardDto RationCard { get; set; } = null!;

    public AadhaarVerificationDto AadhaarVerification { get; set; } = null!;

    public PassbookVerificationDto PassbookVerification { get; set; } = null!;

    public MobileVerificationDto MobileVerification { get; set; } = null!;

    public EntitlementSummaryDto Entitlement { get; set; } = null!;

    public CurrentQrInfoDto? CurrentQr { get; set; }

    public List<CollectionHistoryItemDto> CollectionHistory { get; set; } = [];

    public List<VerificationAuditLogDto> VerificationHistory { get; set; } = [];

    public List<VerificationAuditLogDto> QrScanHistory { get; set; } = [];

    public BeneficiaryRiskInsightDto AIInsight { get; set; } = null!;
}

// Deliberately minimal — the public, unauthenticated view of a beneficiary.
public class PublicBeneficiaryProfileDto
{
    public string BeneficiaryCode { get; set; } = string.Empty;

    public string SchemeCode { get; set; } = string.Empty;

    public string EligibilityBadge { get; set; } = string.Empty; // Eligible | Not Eligible

    public string VerificationBadge { get; set; } = string.Empty; // Verified | Pending

    public string? LastCollectionMonth { get; set; }

    public string ShopCode { get; set; } = string.Empty;

    public string Region { get; set; } = string.Empty; // district/state only — never village/address
}
