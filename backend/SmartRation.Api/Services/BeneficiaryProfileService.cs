using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;
using SmartRation.Api.Services.AI;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Services;

// Everything BeneficiariesController serves: loading a beneficiary with the access rule applied,
// the verification bundle, family, entitlement, collection history and the 360° profile.
// Access rule: a RuralUser sees only their own beneficiary; shop owners, officials and admins see any.
public interface IBeneficiaryProfileService
{
    Task<int> GetMyBeneficiaryIdAsync();
    Task<BeneficiaryProfileDto> GetVerificationAsync(int beneficiaryId);
    Task<FamilyDto> GetFamilyAsync(int beneficiaryId);
    Task<EntitlementSummaryDto> GetEntitlementAsync(int beneficiaryId);
    Task<List<CollectionHistoryItemDto>> GetCollectionHistoryAsync(int beneficiaryId);
    Task<BeneficiaryFullProfileDto> GetFullProfileAsync(int beneficiaryId);
}

public class BeneficiaryProfileService(
    SmartRationDbContext db,
    IAadhaarVerificationService aadhaarService,
    IPassbookVerificationService passbookService,
    IEntitlementService entitlementService,
    IBeneficiaryInsightService beneficiaryInsightService,
    ICurrentUserService currentUser) : IBeneficiaryProfileService
{
    public async Task<int> GetMyBeneficiaryIdAsync() =>
        await db.Beneficiaries
            .Where(b => b.UserId == currentUser.UserId)
            .Select(b => (int?)b.Id)
            .FirstOrDefaultAsync()
        ?? throw new NotFoundException("You do not have a beneficiary profile yet.");

    public async Task<BeneficiaryProfileDto> GetVerificationAsync(int beneficiaryId)
    {
        var beneficiary = await LoadAndAuthorizeAsync(beneficiaryId);

        var aadhaar = await aadhaarService.GetOrCreateAsync(beneficiary.Id);
        var passbook = await passbookService.GetOrCreateAsync(beneficiary.Id);
        var mobile = beneficiary.MobileVerification ?? await EnsureMobileVerificationAsync(beneficiary);

        return new BeneficiaryProfileDto
        {
            Beneficiary = beneficiary.ToDto(),
            Family = beneficiary.Family.ToDto(),
            AadhaarVerification = aadhaar.ToDto(),
            PassbookVerification = passbook.ToDto(),
            MobileVerification = mobile.ToDto()
        };
    }

    public async Task<FamilyDto> GetFamilyAsync(int beneficiaryId) => (await LoadAndAuthorizeAsync(beneficiaryId)).Family.ToDto();

    public async Task<EntitlementSummaryDto> GetEntitlementAsync(int beneficiaryId)
    {
        var beneficiary = await LoadAndAuthorizeAsync(beneficiaryId);
        return await entitlementService.GetEntitlementAsync(beneficiary.FamilyId);
    }

    public async Task<List<CollectionHistoryItemDto>> GetCollectionHistoryAsync(int beneficiaryId)
    {
        await LoadAndAuthorizeAsync(beneficiaryId);
        return (await LoadCollectionsAsync(beneficiaryId)).Select(ToCollectionDto).ToList();
    }

    // Beneficiary 360° — everything one screen needs in a single call.
    public async Task<BeneficiaryFullProfileDto> GetFullProfileAsync(int beneficiaryId)
    {
        var beneficiary = await LoadAndAuthorizeAsync(beneficiaryId);

        var aadhaar = await aadhaarService.GetOrCreateAsync(beneficiary.Id);
        var passbook = await passbookService.GetOrCreateAsync(beneficiary.Id);
        var mobile = beneficiary.MobileVerification ?? await EnsureMobileVerificationAsync(beneficiary);
        var entitlement = await entitlementService.GetEntitlementAsync(beneficiary.FamilyId);
        var aiInsight = await beneficiaryInsightService.GetBeneficiaryInsightAsync(beneficiary.Id);

        var lastCollection = await db.RationCollections
            .Where(c => c.BeneficiaryId == beneficiary.Id)
            .OrderByDescending(c => c.CollectedAt)
            .Select(c => (DateTime?)c.CollectedAt)
            .FirstOrDefaultAsync();

        var confirmedTokens = await db.Tokens
            .Include(t => t.TimeSlot)
            .Include(t => t.RationShop)
            .Where(t => t.UserId == beneficiary.UserId && t.Status == TokenStatus.Confirmed)
            .ToListAsync();
        var upcoming = confirmedTokens
            .Where(t => t.TimeSlot.SlotDate.Date >= DateTime.UtcNow.Date)
            .OrderBy(t => t.TimeSlot.SlotDate)
            .FirstOrDefault();

        var collections = await LoadCollectionsAsync(beneficiary.Id);

        var auditLogs = await db.VerificationAuditLogs
            .Where(l => l.BeneficiaryId == beneficiary.Id)
            .OrderByDescending(l => l.Timestamp)
            .Take(50)
            .ToListAsync();

        var profile = new BeneficiaryProfileDetailsDto
        {
            Id = beneficiary.Id,
            BeneficiaryCode = beneficiary.BeneficiaryCode,
            FullName = beneficiary.User.FullName,
            Gender = beneficiary.Gender.ToString(),
            DateOfBirth = beneficiary.DateOfBirth == default ? null : beneficiary.DateOfBirth.ToString("yyyy-MM-dd"),
            MobileMasked = MaskingUtil.MaskMobile(beneficiary.User.MobileNumber),
            Village = beneficiary.Village,
            District = beneficiary.District,
            State = beneficiary.State,
            Pincode = beneficiary.Pincode,
            ProfilePhotoUrl = beneficiary.ProfilePhotoUrl,
            IsActive = beneficiary.IsActive,
            IsBlocked = beneficiary.IsBlocked,
            RegistrationDate = beneficiary.CreatedAt.ToString("yyyy-MM-dd"),
            LastCollectionDate = lastCollection?.ToString("yyyy-MM-dd"),
            NextCollectionDate = upcoming?.TimeSlot.SlotDate.ToString("yyyy-MM-dd")
        };

        var rationCard = new RationCardDto
        {
            RationCardNumber = passbook.PassbookNumber,
            Status = passbook.Status,
            SchemeCode = beneficiary.Family.RationScheme?.SchemeCode ?? string.Empty,
            SchemeName = beneficiary.Family.RationScheme?.Name ?? string.Empty,
            FamilySize = beneficiary.Family.Members.Count
        };

        var currentQr = upcoming is null ? null : new CurrentQrInfoDto
        {
            TokenId = upcoming.Id,
            TokenNumber = upcoming.TokenNumber,
            QrCodeValue = upcoming.QRCodeValue,
            Status = upcoming.Status.ToString(),
            CollectionDate = upcoming.TimeSlot.SlotDate.ToString("yyyy-MM-dd"),
            BookingTime = upcoming.TimeSlot.StartTime.ToString(@"hh\:mm"),
            ShopName = upcoming.RationShop.ShopName
        };

        return new BeneficiaryFullProfileDto
        {
            Profile = profile,
            Family = beneficiary.Family.ToDto(),
            RationCard = rationCard,
            AadhaarVerification = aadhaar.ToDto(),
            PassbookVerification = passbook.ToDto(),
            MobileVerification = mobile.ToDto(),
            Entitlement = entitlement,
            CurrentQr = currentQr,
            CollectionHistory = collections.Select(ToCollectionDto).ToList(),
            VerificationHistory = auditLogs.Select(ToAuditDto).ToList(),
            QrScanHistory = auditLogs.Where(l => l.Action == VerificationAction.QrScanned).Select(ToAuditDto).ToList(),
            AIInsight = aiInsight
        };
    }

    private Task<List<RationCollection>> LoadCollectionsAsync(int beneficiaryId) =>
        db.RationCollections
            .Include(c => c.Items)
            .Include(c => c.RationShop)
            .Where(c => c.BeneficiaryId == beneficiaryId)
            .OrderByDescending(c => c.CollectedAt)
            .ToListAsync();

    private static CollectionHistoryItemDto ToCollectionDto(RationCollection c) => new()
    {
        CollectionCode = c.CollectionCode,
        CollectedAt = c.CollectedAt.ToString("yyyy-MM-dd HH:mm"),
        ShopName = c.RationShop.ShopName,
        Items = c.Items.Select(i => new CollectedItemDto { RationType = i.RationType.ToString(), Quantity = i.Quantity }).ToList()
    };

    private static VerificationAuditLogDto ToAuditDto(VerificationAuditLog l) => new()
    {
        Id = l.Id,
        VerificationReference = l.VerificationReference,
        TokenNumber = l.TokenNumber,
        BeneficiaryId = l.BeneficiaryId,
        ShopId = l.ShopId,
        Action = l.Action.ToString(),
        VerificationMethod = l.VerificationMethod,
        Status = l.Status,
        Reason = l.Reason,
        OperatorId = l.OperatorId,
        Timestamp = l.Timestamp.ToString("yyyy-MM-dd HH:mm:ss")
    };

    private async Task<Beneficiary> LoadAndAuthorizeAsync(int beneficiaryId)
    {
        var beneficiary = await db.Beneficiaries
            .Include(b => b.User)
            .Include(b => b.Family).ThenInclude(f => f.Members)
            .Include(b => b.Family).ThenInclude(f => f.RationScheme)
            .Include(b => b.MobileVerification)
            .FirstOrDefaultAsync(b => b.Id == beneficiaryId)
            ?? throw new NotFoundException("Beneficiary not found.");

        var allowed = currentUser.Role switch
        {
            UserRole.RuralUser => beneficiary.UserId == currentUser.UserId,
            UserRole.ShopOwner or UserRole.GovernmentOfficial or UserRole.Admin => true,
            _ => false
        };

        if (!allowed)
        {
            throw new ForbiddenException("You do not have access to this beneficiary.");
        }

        return beneficiary;
    }

    private async Task<Models.MobileVerification> EnsureMobileVerificationAsync(Beneficiary beneficiary)
    {
        var mobile = new Models.MobileVerification
        {
            BeneficiaryId = beneficiary.Id,
            MobileMasked = MaskingUtil.MaskMobile(beneficiary.User.MobileNumber),
            Status = Models.MobileVerificationStatus.NotVerified,
            VerificationSource = "SYNTHETIC_DEMO"
        };
        db.MobileVerifications.Add(mobile);
        await db.SaveChangesAsync();
        return mobile;
    }
}
