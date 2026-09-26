using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Services;

// A family and its monthly entitlement (FamiliesController), behind the shared access rule.
public interface IFamilyService
{
    Task<FamilyDto> GetFamilyAsync(int familyId);
    Task<EntitlementSummaryDto> GetEntitlementAsync(int familyId);
}

public class FamilyService(SmartRationDbContext db, IEntitlementService entitlementService, ICurrentUserService currentUser) : IFamilyService
{
    public async Task<FamilyDto> GetFamilyAsync(int familyId) => (await LoadVisibleAsync(familyId, includeMembers: true)).ToDto();

    public async Task<EntitlementSummaryDto> GetEntitlementAsync(int familyId)
    {
        await LoadVisibleAsync(familyId, includeMembers: false);
        return await entitlementService.GetEntitlementAsync(familyId);
    }

    private async Task<Family> LoadVisibleAsync(int familyId, bool includeMembers)
    {
        var query = db.Families.Include(f => f.Beneficiaries).AsQueryable();
        if (includeMembers)
        {
            query = query.Include(f => f.Members);
        }
        var family = await query.FirstOrDefaultAsync(f => f.Id == familyId)
            ?? throw new NotFoundException("Family not found.");
        if (!BeneficiaryAccess.CanSeeFamily(currentUser, family.Beneficiaries.Select(b => b.UserId)))
        {
            throw new ForbiddenException("You do not have access to this family.");
        }
        return family;
    }
}
