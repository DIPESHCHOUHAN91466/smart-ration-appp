using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

// The anonymous public verification badge (PublicController). Returns ONLY non-sensitive fields:
// never Aadhaar, mobile, full address, family members or anything that needs a login.
public interface IPublicProfileService
{
    Task<PublicBeneficiaryProfileDto> GetAsync(string publicReference);
}

public class PublicProfileService(SmartRationDbContext db) : IPublicProfileService
{
    public async Task<PublicBeneficiaryProfileDto> GetAsync(string publicReference)
    {
        var beneficiary = await db.Beneficiaries
            .Include(b => b.Family).ThenInclude(f => f.Members)
            .Include(b => b.Family).ThenInclude(f => f.RationScheme)
            .Include(b => b.Family).ThenInclude(f => f.RationShop)
            .FirstOrDefaultAsync(b => b.BeneficiaryCode == publicReference)
            ?? throw new NotFoundException("No beneficiary found for this reference.");

        var eligibleCount = beneficiary.Family.Members.Count(m => m.Eligibility == EligibilityStatus.Eligible);
        var lastCollection = await db.RationCollections
            .Where(c => c.BeneficiaryId == beneficiary.Id)
            .OrderByDescending(c => c.CollectedAt)
            .Select(c => (DateTime?)c.CollectedAt)
            .FirstOrDefaultAsync();

        return new PublicBeneficiaryProfileDto
        {
            BeneficiaryCode = beneficiary.BeneficiaryCode,
            SchemeCode = beneficiary.Family.RationScheme.SchemeCode,
            EligibilityBadge = eligibleCount > 0 ? "Eligible" : "Not Eligible",
            VerificationBadge = beneficiary.IsActive && !beneficiary.IsBlocked ? "Verified" : "Pending",
            LastCollectionMonth = lastCollection?.ToString("MMMM yyyy"),
            ShopCode = beneficiary.Family.RationShop.ShopCode,
            Region = $"{beneficiary.District}, {beneficiary.State}"
        };
    }
}
