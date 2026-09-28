using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.AI;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/ai")]
[Authorize]
public class AIController(
    IAIIntelligenceService intelligenceService,
    IShopInsightService shopInsightService,
    IBeneficiaryInsightService beneficiaryInsightService,
    IDemandForecastService demandForecastService,
    IInventoryRiskService inventoryRiskService,
    IQueuePredictionService queuePredictionService,
    IAnomalyDetectionService anomalyDetectionService,
    IPythonAiClient pythonAi,
    IBeneficiaryProfileService profiles,
    ICurrentUserService currentUser) : ControllerBase
{
    [HttpGet("intelligence-center")]
    [Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<AIIntelligenceCenterDto>>> GetIntelligenceCenter()
    {
        var result = await intelligenceService.GetIntelligenceCenterAsync();
        return Ok(ApiResponse<AIIntelligenceCenterDto>.Ok(result));
    }

    [HttpGet("demand-forecast")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<List<DemandForecastDto>>>> GetDemandForecast([FromQuery] int? shopId)
    {
        var effectiveShopId = await ResolveShopScopeAsync(shopId);
        var result = await demandForecastService.GetForecastAsync(effectiveShopId);
        return Ok(ApiResponse<List<DemandForecastDto>>.Ok(result));
    }

    [HttpGet("inventory-risk")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<List<InventoryRiskDto>>>> GetInventoryRisk([FromQuery] int? shopId)
    {
        var effectiveShopId = await ResolveShopScopeAsync(shopId);
        var result = await inventoryRiskService.GetRisksAsync(effectiveShopId);
        return Ok(ApiResponse<List<InventoryRiskDto>>.Ok(result));
    }

    [HttpGet("queue-prediction")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<List<QueuePredictionDto>>>> GetQueuePrediction([FromQuery] int? shopId)
    {
        var effectiveShopId = await ResolveShopScopeAsync(shopId);
        var result = await queuePredictionService.GetPredictionsAsync(effectiveShopId);
        return Ok(ApiResponse<List<QueuePredictionDto>>.Ok(result));
    }

    [HttpGet("alerts")]
    [Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)},{nameof(UserRole.ShopOwner)}")]
    public async Task<ActionResult<ApiResponse<List<AIAlert>>>> GetAlerts()
    {
        var alerts = await anomalyDetectionService.GetRecentAlertsAsync();
        if (currentUser.Role == UserRole.ShopOwner)
        {
            alerts = alerts.Where(a => a.ShopId == currentUser.RationShopId).ToList();
        }
        return Ok(ApiResponse<List<AIAlert>>.Ok(alerts));
    }

    [HttpGet("shops/{shopId:int}/insight")]
    [Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)},{nameof(UserRole.ShopOwner)}")]
    public async Task<ActionResult<ApiResponse<ShopRiskInsightDto>>> GetShopInsight(int shopId)
    {
        if (currentUser.Role == UserRole.ShopOwner && currentUser.RationShopId != shopId)
        {
            throw new ForbiddenException("You can only view insights for your own shop.");
        }

        var result = await shopInsightService.GetShopInsightAsync(shopId);
        return Ok(ApiResponse<ShopRiskInsightDto>.Ok(result));
    }

    [HttpGet("beneficiaries/{beneficiaryId:int}/insight")]
    public async Task<ActionResult<ApiResponse<BeneficiaryRiskInsightDto>>> GetBeneficiaryInsight(int beneficiaryId)
    {
        await profiles.EnsureCanSeeAsync(beneficiaryId); // shared BeneficiaryAccess rule

        var result = await beneficiaryInsightService.GetBeneficiaryInsightAsync(beneficiaryId);
        return Ok(ApiResponse<BeneficiaryRiskInsightDto>.Ok(result));
    }

    // ---- Python AI analytics (optional service; see ai) ----
    // Shop owners are always scoped to their own shop. Beneficiaries have no access.

    [HttpGet("analytics/forecast")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<AiAnalyticsResponseDto>>> AnalyticsForecast(
        [FromQuery] int? shopId, [FromQuery] int horizonDays = 7, [FromQuery] string lang = "en", CancellationToken ct = default)
    {
        var scope = await ResolveShopScopeAsync(shopId);
        var result = await pythonAi.GetAsync("/v1/forecast", Query(scope, lang, ("horizon_days", Math.Clamp(horizonDays, 1, 90).ToString())), ct);
        // Fallback keeps the built-in month-over-month forecast available if the AI service is down.
        return Ok(ApiResponse<AiAnalyticsResponseDto>.Ok(await WithFallbackAsync(result, () => demandForecastService.GetForecastAsync(scope))));
    }

    [HttpGet("analytics/inventory")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<AiAnalyticsResponseDto>>> AnalyticsInventory(
        [FromQuery] int? shopId, [FromQuery] string lang = "en", CancellationToken ct = default)
    {
        var scope = await ResolveShopScopeAsync(shopId);
        var result = await pythonAi.GetAsync("/v1/inventory", Query(scope, lang), ct);
        return Ok(ApiResponse<AiAnalyticsResponseDto>.Ok(await WithFallbackAsync(result, () => inventoryRiskService.GetRisksAsync(scope))));
    }

    [HttpGet("analytics/queue")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<AiAnalyticsResponseDto>>> AnalyticsQueue(
        [FromQuery] int? shopId, [FromQuery] string lang = "en", CancellationToken ct = default)
    {
        var scope = await ResolveShopScopeAsync(shopId);
        var result = await pythonAi.GetAsync("/v1/queue", Query(scope, lang), ct);
        return Ok(ApiResponse<AiAnalyticsResponseDto>.Ok(await WithFallbackAsync(result, () => queuePredictionService.GetPredictionsAsync(scope))));
    }

    [HttpGet("analytics/risk")]
    [Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<AiAnalyticsResponseDto>>> AnalyticsRisk(
        [FromQuery] int? shopId, [FromQuery] int limit = 25, [FromQuery] string lang = "en", CancellationToken ct = default)
    {
        var result = await pythonAi.GetAsync("/v1/risk/beneficiaries", Query(shopId, lang, ("limit", Math.Clamp(limit, 1, 200).ToString())), ct);
        return Ok(ApiResponse<AiAnalyticsResponseDto>.Ok(ToDto(result)));
    }

    [HttpGet("analytics/shops")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<AiAnalyticsResponseDto>>> AnalyticsShops(
        [FromQuery] int? shopId, [FromQuery] string lang = "en", CancellationToken ct = default)
    {
        var scope = await ResolveShopScopeAsync(shopId);
        var result = await pythonAi.GetAsync("/v1/shops/monitor", Query(scope, lang), ct);
        return Ok(ApiResponse<AiAnalyticsResponseDto>.Ok(ToDto(result)));
    }

    private static Dictionary<string, string?> Query(int? shopId, string lang, params (string Key, string Value)[] extra)
    {
        var query = new Dictionary<string, string?>
        {
            ["shop_id"] = shopId?.ToString(),
            ["lang"] = lang is "hi" or "mr" ? lang : "en"
        };
        foreach (var (key, value) in extra)
        {
            query[key] = value;
        }
        return query;
    }

    private static AiAnalyticsResponseDto ToDto(PythonAiResult result) => result.Available
        ? new AiAnalyticsResponseDto { Available = true, Source = "python-ai", Data = result.Data }
        : new AiAnalyticsResponseDto { Available = false, Source = "unavailable", ErrorCode = result.ErrorCode, Message = result.Message };

    private static async Task<AiAnalyticsResponseDto> WithFallbackAsync<T>(PythonAiResult result, Func<Task<T>> fallback)
    {
        var dto = ToDto(result);
        if (!dto.Available)
        {
            dto.Source = "fallback";
            dto.Fallback = await fallback();
        }
        return dto;
    }

    private Task<int?> ResolveShopScopeAsync(int? requestedShopId)
    {
        if (currentUser.Role == UserRole.ShopOwner)
        {
            return Task.FromResult(currentUser.RationShopId);
        }

        return Task.FromResult(requestedShopId);
    }
}
