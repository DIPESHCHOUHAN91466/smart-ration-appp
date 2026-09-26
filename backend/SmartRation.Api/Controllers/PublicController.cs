using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

// Unauthenticated by design — exposes only the minimal, non-sensitive
// fields a public verification badge needs. Never Aadhaar, mobile, full
// address, family details, or anything requiring a login (PublicProfileService).
[ApiController]
[Route("api/public")]
[AllowAnonymous]
public class PublicController(IPublicProfileService publicProfiles) : ControllerBase
{
    [HttpGet("beneficiaries/{publicReference}")]
    public async Task<ActionResult<ApiResponse<PublicBeneficiaryProfileDto>>> GetPublicProfile(string publicReference) =>
        Ok(ApiResponse<PublicBeneficiaryProfileDto>.Ok(await publicProfiles.GetAsync(publicReference)));
}
