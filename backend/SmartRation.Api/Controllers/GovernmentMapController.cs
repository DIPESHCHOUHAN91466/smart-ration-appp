using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Map;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/government/map")]
[Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class GovernmentMapController(IMapService mapService) : ControllerBase
{
    [HttpGet("analytics")]
    public async Task<ActionResult<ApiResponse<MapAnalyticsDto>>> GetAnalytics()
    {
        var analytics = await mapService.GetAnalyticsAsync();
        return Ok(ApiResponse<MapAnalyticsDto>.Ok(analytics));
    }
}
