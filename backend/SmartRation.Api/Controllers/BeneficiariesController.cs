using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/beneficiaries")]
[Authorize]
public class BeneficiariesController(
    SmartRationDbContext db,
    IAadhaarVerificationService aadhaarService,
    IPassbookVerificationService passbookService,
    IEntitlementService entitlementService,
    ICurrentUserService currentUser) : ControllerBase
{
    [HttpGet("me")]
    [Authorize(Roles = nameof(UserRole.RuralUser))]
    public async Task<ActionResult<ApiResponse<BeneficiaryProfileDto>>> GetMyProfile()
    {
        var beneficiaryId = await db.Beneficiaries
            .Where(b => b.UserId == currentUser.UserId)
            .Select(b => (int?)b.Id)
            .FirstOrDefaultAsync()
            ?? throw new NotFoundException("You do not have a beneficiary profile yet.");

        return await GetVerification(beneficiaryId);
    }

    [HttpGet("{id:int}/verification")]
    public async Task<ActionResult<ApiResponse<BeneficiaryProfileDto>>> GetVerification(int id)
    {
        var beneficiary = await LoadAndAuthorizeAsync(id);

        var aadhaar = await aadhaarService.GetOrCreateAsync(beneficiary.Id);
        var passbook = await passbookService.GetOrCreateAsync(beneficiary.Id);
        var mobile = beneficiary.MobileVerification ?? await EnsureMobileVerificationAsync(beneficiary);

        return Ok(ApiResponse<BeneficiaryProfileDto>.Ok(new BeneficiaryProfileDto
        {
            Beneficiary = beneficiary.ToDto(),
            Family = beneficiary.Family.ToDto(),
            AadhaarVerification = aadhaar.ToDto(),
            PassbookVerification = passbook.ToDto(),
            MobileVerification = mobile.ToDto()
        }));
    }

    [HttpGet("{id:int}/family")]
    public async Task<ActionResult<ApiResponse<FamilyDto>>> GetFamily(int id)
    {
        var beneficiary = await LoadAndAuthorizeAsync(id);
        return Ok(ApiResponse<FamilyDto>.Ok(beneficiary.Family.ToDto()));
    }

    [HttpGet("{id:int}/entitlement")]
    public async Task<ActionResult<ApiResponse<EntitlementSummaryDto>>> GetEntitlement(int id)
    {
        var beneficiary = await LoadAndAuthorizeAsync(id);
        var entitlement = await entitlementService.GetEntitlementAsync(beneficiary.FamilyId);
        return Ok(ApiResponse<EntitlementSummaryDto>.Ok(entitlement));
    }

    [HttpGet("{id:int}/collections")]
    public async Task<ActionResult<ApiResponse<List<CollectionHistoryItemDto>>>> GetCollectionHistory(int id)
    {
        await LoadAndAuthorizeAsync(id);

        var collections = await db.RationCollections
            .Include(c => c.Items)
            .Include(c => c.RationShop)
            .Where(c => c.BeneficiaryId == id)
            .OrderByDescending(c => c.CollectedAt)
            .ToListAsync();

        var result = collections.Select(c => new CollectionHistoryItemDto
        {
            CollectionCode = c.CollectionCode,
            CollectedAt = c.CollectedAt.ToString("yyyy-MM-dd HH:mm"),
            ShopName = c.RationShop.ShopName,
            Items = c.Items.Select(i => new CollectedItemDto { RationType = i.RationType.ToString(), Quantity = i.Quantity }).ToList()
        }).ToList();

        return Ok(ApiResponse<List<CollectionHistoryItemDto>>.Ok(result));
    }

    private async Task<Beneficiary> LoadAndAuthorizeAsync(int beneficiaryId)
    {
        var beneficiary = await db.Beneficiaries
            .Include(b => b.User)
            .Include(b => b.Family).ThenInclude(f => f.Members)
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
