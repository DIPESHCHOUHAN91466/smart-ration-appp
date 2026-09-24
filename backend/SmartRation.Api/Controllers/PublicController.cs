using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;

namespace SmartRation.Api.Controllers;

// Unauthenticated by design — exposes only the minimal, non-sensitive
// fields a public verification badge needs. Never Aadhaar, mobile, full
// address, family details, or anything requiring a login.
[ApiController]
[Route("api/public")]
[AllowAnonymous]
public class PublicController(SmartRationDbContext db) : ControllerBase
{
    [HttpGet("beneficiaries/{publicReference}")]
    public async Task<ActionResult<ApiResponse<PublicBeneficiaryProfileDto>>> GetPublicProfile(string publicReference)
    {
        var beneficiary = await db.Beneficiaries
            .Include(b => b.Family).ThenInclude(f => f.Members)
            .Include(b => b.Family).ThenInclude(f => f.RationScheme)
            .Include(b => b.Family).ThenInclude(f => f.RationShop)
            .FirstOrDefaultAsync(b => b.BeneficiaryCode == publicReference)
            ?? throw new NotFoundException("No beneficiary found for this reference.");

        var eligibleCount = beneficiary.Family.Members.Count(m => m.Eligibility == EligibilityStatus.Eligible);

        var lastCollectionMonth = await db.RationCollections
            .Where(c => c.BeneficiaryId == beneficiary.Id)
            .OrderByDescending(c => c.CollectedAt)
            .Select(c => (DateTime?)c.CollectedAt)
            .FirstOrDefaultAsync();

        return Ok(ApiResponse<PublicBeneficiaryProfileDto>.Ok(new PublicBeneficiaryProfileDto
        {
            BeneficiaryCode = beneficiary.BeneficiaryCode,
            SchemeCode = beneficiary.Family.RationScheme.SchemeCode,
            EligibilityBadge = eligibleCount > 0 ? "Eligible" : "Not Eligible",
            VerificationBadge = beneficiary.IsActive && !beneficiary.IsBlocked ? "Verified" : "Pending",
            LastCollectionMonth = lastCollectionMonth?.ToString("MMMM yyyy"),
            ShopCode = beneficiary.Family.RationShop.ShopCode,
            Region = $"{beneficiary.District}, {beneficiary.State}"
        }));
    }
}
