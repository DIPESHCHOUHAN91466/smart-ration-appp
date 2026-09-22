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
[Route("api/families")]
[Authorize]
public class FamiliesController(
    SmartRationDbContext db,
    IEntitlementService entitlementService,
    ICurrentUserService currentUser) : ControllerBase
{
    [HttpGet("{id:int}/entitlement")]
    public async Task<ActionResult<ApiResponse<EntitlementSummaryDto>>> GetEntitlement(int id)
    {
        var family = await db.Families
            .Include(f => f.Beneficiaries)
            .FirstOrDefaultAsync(f => f.Id == id)
            ?? throw new NotFoundException("Family not found.");

        var allowed = currentUser.Role switch
        {
            UserRole.RuralUser => family.Beneficiaries.Any(b => b.UserId == currentUser.UserId),
            UserRole.ShopOwner or UserRole.GovernmentOfficial or UserRole.Admin => true,
            _ => false
        };

        if (!allowed)
        {
            throw new ForbiddenException("You do not have access to this family.");
        }

        var entitlement = await entitlementService.GetEntitlementAsync(id);
        return Ok(ApiResponse<EntitlementSummaryDto>.Ok(entitlement));
    }

    [HttpGet("{id:int}")]
    public async Task<ActionResult<ApiResponse<FamilyDto>>> GetFamily(int id)
    {
        var family = await db.Families
            .Include(f => f.Members)
            .Include(f => f.Beneficiaries)
            .FirstOrDefaultAsync(f => f.Id == id)
            ?? throw new NotFoundException("Family not found.");

        var allowed = currentUser.Role switch
        {
            UserRole.RuralUser => family.Beneficiaries.Any(b => b.UserId == currentUser.UserId),
            UserRole.ShopOwner or UserRole.GovernmentOfficial or UserRole.Admin => true,
            _ => false
        };

        if (!allowed)
        {
            throw new ForbiddenException("You do not have access to this family.");
        }

        return Ok(ApiResponse<FamilyDto>.Ok(family.ToDto()));
    }
}
