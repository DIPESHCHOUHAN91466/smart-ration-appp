using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

// HTTP only: routing, roles and response envelopes. Loading, the per-beneficiary access rule and
// the profile assembly live in BeneficiaryProfileService.
[ApiController]
[Route("api/beneficiaries")]
[Authorize]
public class BeneficiariesController(IBeneficiaryProfileService profiles) : ControllerBase
{
    [HttpGet("me")]
    [Authorize(Roles = nameof(UserRole.RuralUser))]
    public async Task<ActionResult<ApiResponse<BeneficiaryProfileDto>>> GetMyProfile() =>
        await GetVerification(await profiles.GetMyBeneficiaryIdAsync());

    [HttpGet("{id:int}/verification")]
    public async Task<ActionResult<ApiResponse<BeneficiaryProfileDto>>> GetVerification(int id) =>
        Ok(ApiResponse<BeneficiaryProfileDto>.Ok(await profiles.GetVerificationAsync(id)));

    [HttpGet("{id:int}/family")]
    public async Task<ActionResult<ApiResponse<FamilyDto>>> GetFamily(int id) =>
        Ok(ApiResponse<FamilyDto>.Ok(await profiles.GetFamilyAsync(id)));

    [HttpGet("{id:int}/entitlement")]
    public async Task<ActionResult<ApiResponse<EntitlementSummaryDto>>> GetEntitlement(int id) =>
        Ok(ApiResponse<EntitlementSummaryDto>.Ok(await profiles.GetEntitlementAsync(id)));

    [HttpGet("{id:int}/collections")]
    public async Task<ActionResult<ApiResponse<List<CollectionHistoryItemDto>>>> GetCollectionHistory(int id) =>
        Ok(ApiResponse<List<CollectionHistoryItemDto>>.Ok(await profiles.GetCollectionHistoryAsync(id)));

    // Beneficiary 360° — everything one screen needs in a single call.
    [HttpGet("{id:int}/full-profile")]
    public async Task<ActionResult<ApiResponse<BeneficiaryFullProfileDto>>> GetFullProfile(int id) =>
        Ok(ApiResponse<BeneficiaryFullProfileDto>.Ok(await profiles.GetFullProfileAsync(id)));
}
