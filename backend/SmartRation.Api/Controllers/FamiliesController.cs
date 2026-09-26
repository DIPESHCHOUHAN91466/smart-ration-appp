using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

// A family and its entitlement. Access rule and loading: FamilyService (BeneficiaryAccess).
[ApiController]
[Route("api/families")]
[Authorize]
public class FamiliesController(IFamilyService families) : ControllerBase
{
    [HttpGet("{id:int}/entitlement")]
    public async Task<ActionResult<ApiResponse<EntitlementSummaryDto>>> GetEntitlement(int id) =>
        Ok(ApiResponse<EntitlementSummaryDto>.Ok(await families.GetEntitlementAsync(id)));

    [HttpGet("{id:int}")]
    public async Task<ActionResult<ApiResponse<FamilyDto>>> GetFamily(int id) =>
        Ok(ApiResponse<FamilyDto>.Ok(await families.GetFamilyAsync(id)));
}
