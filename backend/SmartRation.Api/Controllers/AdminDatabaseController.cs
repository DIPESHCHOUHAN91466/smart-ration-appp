using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Admin;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

// Read-only development/admin database viewer. Never exposed to RuralUser
// or ShopOwner — Government/Admin only, and intentionally read-only (no
// write actions exist on this controller). Queries live in AdminDatabaseBrowserService.
[ApiController]
[Route("api/admin/database")]
[Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class AdminDatabaseController(IAdminDatabaseBrowserService browser) : ControllerBase
{
    private static readonly string[] SupportedTables =
    [
        "beneficiaries", "familyMembers", "tokens", "collections", "inventory", "aiInsights", "auditLogs"
    ];

    [HttpGet("tables")]
    public ActionResult<ApiResponse<string[]>> GetTables() => Ok(ApiResponse<string[]>.Ok(SupportedTables));

    [HttpGet("{table}")]
    public async Task<ActionResult> GetTable(string table, [FromQuery] string? search, [FromQuery] int page = 1, [FromQuery] int pageSize = 25)
    {
        page = Math.Max(1, page);
        pageSize = Math.Clamp(pageSize, 1, 100);

        return table.ToLowerInvariant() switch
        {
            "beneficiaries" => Ok(ApiResponse<PagedResultDto<SyntheticBeneficiaryRowDto>>.Ok(await browser.GetBeneficiariesAsync(search, page, pageSize))),
            "familymembers" => Ok(ApiResponse<PagedResultDto<FamilyMemberRowDto>>.Ok(await browser.GetFamilyMembersAsync(search, page, pageSize))),
            "tokens" => Ok(ApiResponse<PagedResultDto<TokenRowDto>>.Ok(await browser.GetTokensAsync(search, page, pageSize))),
            "collections" => Ok(ApiResponse<PagedResultDto<CollectionRowDto>>.Ok(await browser.GetCollectionsAsync(search, page, pageSize))),
            "inventory" => Ok(ApiResponse<PagedResultDto<InventoryRowDto>>.Ok(await browser.GetInventoryAsync(page, pageSize))),
            "aiinsights" => Ok(ApiResponse<PagedResultDto<AIInsightRowDto>>.Ok(await browser.GetAIInsightsAsync(page, pageSize))),
            "auditlogs" => Ok(ApiResponse<PagedResultDto<VerificationAuditLogDto>>.Ok(await browser.GetAuditLogsAsync(page, pageSize))),
            _ => NotFound(ApiResponse.Fail($"Unknown table '{table}'. Supported: {string.Join(", ", SupportedTables)}"))
        };
    }
}
