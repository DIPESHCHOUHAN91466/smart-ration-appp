using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.AI;

namespace SmartRation.Api.Controllers;

// Persisted AI alerts (built-in rules + Python AI). Scoping is enforced in
// AiAlertService: shop owners only ever get their own shop's alerts no matter
// what shopId they send; beneficiaries have no access at all.
// (The older GET /api/ai/alerts on AIController is unchanged.)
[ApiController]
[Route("api/ai/alerts")]
[Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class AIAlertsController(IAiAlertService alerts, ICurrentUserService currentUser) : ControllerBase
{
    // All alerts (filterable). status: all | active | Open | UnderReview | Resolved | Dismissed
    [HttpGet("list")]
    public async Task<ActionResult<ApiResponse<List<AiAlertDto>>>> List(
        [FromQuery] string? status, [FromQuery] int? shopId, [FromQuery] string? source, [FromQuery] int limit = 100)
    {
        var result = await alerts.ListAsync(new AiAlertQuery(status, shopId, source, limit));
        return Ok(ApiResponse<List<AiAlertDto>>.Ok(result));
    }

    // Open + under-review alerts. Runs a throttled refresh from the AI service
    // first (at most every 5 minutes; repeated calls never duplicate alerts).
    [HttpGet("active")]
    public async Task<ActionResult<ApiResponse<ActiveAlertsDto>>> Active([FromQuery] int? shopId, CancellationToken ct)
    {
        var sync = await alerts.SyncFromPythonAsync(force: false, ct);
        var items = await alerts.ListAsync(new AiAlertQuery("active", shopId, null, 200));
        return Ok(ApiResponse<ActiveAlertsDto>.Ok(new ActiveAlertsDto { Sync = sync, Items = items }));
    }

    [HttpGet("shop/{shopId:int}")]
    public async Task<ActionResult<ApiResponse<List<AiAlertDto>>>> ByShop(int shopId, [FromQuery] string? status = "active")
    {
        if (currentUser.Role == UserRole.ShopOwner && currentUser.RationShopId != shopId)
        {
            throw new ForbiddenException("You can only view alerts for your own shop.");
        }
        var result = await alerts.ListAsync(new AiAlertQuery(status, shopId, null, 200));
        return Ok(ApiResponse<List<AiAlertDto>>.Ok(result));
    }

    [HttpGet("{id:int}")]
    public async Task<ActionResult<ApiResponse<AiAlertDto>>> Detail(int id) =>
        Ok(ApiResponse<AiAlertDto>.Ok(await alerts.GetAsync(id)));

    [HttpPost("{id:int}/resolve")]
    [Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<AiAlertDto>>> Resolve(int id, ResolveAiAlertRequestDto request) =>
        Ok(ApiResponse<AiAlertDto>.Ok(await alerts.ResolveAsync(id, request), "Alert updated"));

    // Forces an immediate re-analysis (still deduplicated).
    [HttpPost("sync")]
    [Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<AiAlertSyncResultDto>>> Sync(CancellationToken ct) =>
        Ok(ApiResponse<AiAlertSyncResultDto>.Ok(await alerts.SyncFromPythonAsync(force: true, ct)));
}

public class ActiveAlertsDto
{
    public AiAlertSyncResultDto Sync { get; set; } = new();
    public List<AiAlertDto> Items { get; set; } = [];
}
