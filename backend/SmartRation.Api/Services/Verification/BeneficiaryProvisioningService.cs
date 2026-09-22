using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

public class BeneficiaryProvisioningService(
    SmartRationDbContext db,
    IAadhaarVerificationService aadhaarService,
    IPassbookVerificationService passbookService) : IBeneficiaryProvisioningService
{
    public async Task<Beneficiary> ProvisionAsync(User user, int? rationShopId = null, int? rationSchemeId = null, string? address = null)
    {
        var shopId = rationShopId ?? await db.RationShops
            .Where(s => s.IsActive)
            .OrderBy(s => s.Id)
            .Select(s => s.Id)
            .FirstOrDefaultAsync();

        if (shopId == 0)
        {
            throw new BadRequestException("No active ration shop is configured to assign this beneficiary to.");
        }

        var schemeId = rationSchemeId ?? await db.RationSchemes
            .Where(s => s.SchemeCode == "DEMO-NFSA" && s.IsActive)
            .Select(s => s.Id)
            .FirstOrDefaultAsync();

        if (schemeId == 0)
        {
            throw new BadRequestException("No active ration scheme is configured to assign this beneficiary to.");
        }

        var family = new Family
        {
            FamilyCode = string.Empty,
            RationShopId = shopId,
            RationSchemeId = schemeId,
            DataSource = "SYNTHETIC_DEMO"
        };
        db.Families.Add(family);
        await db.SaveChangesAsync();

        family.FamilyCode = $"FAM-DEMO-{family.Id:D4}";

        db.FamilyMembers.Add(new FamilyMember
        {
            FamilyId = family.Id,
            FullName = user.FullName,
            Age = 30,
            Relationship = FamilyRelationship.Head,
            Eligibility = EligibilityStatus.Eligible,
            DataSource = "SYNTHETIC_DEMO"
        });

        var beneficiary = new Beneficiary
        {
            BeneficiaryCode = string.Empty,
            Address = address ?? "Demo Village",
            UserId = user.Id,
            FamilyId = family.Id,
            IsActive = true,
            IsBlocked = false,
            DataSource = "SYNTHETIC_DEMO"
        };
        db.Beneficiaries.Add(beneficiary);
        await db.SaveChangesAsync();

        beneficiary.BeneficiaryCode = $"BEN-DEMO-{beneficiary.Id:D4}";

        db.MobileVerifications.Add(new MobileVerification
        {
            BeneficiaryId = beneficiary.Id,
            MobileMasked = MaskingUtil.MaskMobile(user.MobileNumber),
            Status = MobileVerificationStatus.Verified,
            VerifiedAt = DateTime.UtcNow,
            VerificationSource = "SYNTHETIC_DEMO"
        });

        await db.SaveChangesAsync();

        await aadhaarService.GetOrCreateAsync(beneficiary.Id);
        await passbookService.GetOrCreateAsync(beneficiary.Id);

        return beneficiary;
    }
}
