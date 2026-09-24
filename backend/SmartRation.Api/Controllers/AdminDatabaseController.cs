using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Admin;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;

namespace SmartRation.Api.Controllers;

// Read-only development/admin database viewer. Never exposed to RuralUser
// or ShopOwner — Government/Admin only, and intentionally read-only (no
// write actions exist on this controller).
[ApiController]
[Route("api/admin/database")]
[Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class AdminDatabaseController(SmartRationDbContext db) : ControllerBase
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
            "beneficiaries" => Ok(ApiResponse<PagedResultDto<SyntheticBeneficiaryRowDto>>.Ok(await GetBeneficiariesAsync(search, page, pageSize))),
            "familymembers" => Ok(ApiResponse<PagedResultDto<FamilyMemberRowDto>>.Ok(await GetFamilyMembersAsync(search, page, pageSize))),
            "tokens" => Ok(ApiResponse<PagedResultDto<TokenRowDto>>.Ok(await GetTokensAsync(search, page, pageSize))),
            "collections" => Ok(ApiResponse<PagedResultDto<CollectionRowDto>>.Ok(await GetCollectionsAsync(search, page, pageSize))),
            "inventory" => Ok(ApiResponse<PagedResultDto<InventoryRowDto>>.Ok(await GetInventoryAsync(page, pageSize))),
            "aiinsights" => Ok(ApiResponse<PagedResultDto<AIInsightRowDto>>.Ok(await GetAIInsightsAsync(page, pageSize))),
            "auditlogs" => Ok(ApiResponse<PagedResultDto<VerificationAuditLogDto>>.Ok(await GetAuditLogsAsync(page, pageSize))),
            _ => NotFound(ApiResponse.Fail($"Unknown table '{table}'. Supported: {string.Join(", ", SupportedTables)}"))
        };
    }

    private async Task<PagedResultDto<SyntheticBeneficiaryRowDto>> GetBeneficiariesAsync(string? search, int page, int pageSize)
    {
        var query = db.Beneficiaries
            .Include(b => b.User)
            .Include(b => b.Family).ThenInclude(f => f.Members)
            .Include(b => b.Family).ThenInclude(f => f.RationScheme)
            .Include(b => b.Family).ThenInclude(f => f.RationShop)
            .Include(b => b.AadhaarVerification)
            .Include(b => b.PassbookVerification)
            .AsQueryable();

        if (!string.IsNullOrWhiteSpace(search))
        {
            var term = search.Trim().ToLowerInvariant();
            query = query.Where(b => b.BeneficiaryCode.ToLower().Contains(term) || b.User.FullName.ToLower().Contains(term));
        }

        var totalCount = await query.CountAsync();
        var items = await query.OrderBy(b => b.Id).Skip((page - 1) * pageSize).Take(pageSize).ToListAsync();

        return new PagedResultDto<SyntheticBeneficiaryRowDto>
        {
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
            Items = items.Select(b => new SyntheticBeneficiaryRowDto
            {
                Id = b.Id,
                BeneficiaryCode = b.BeneficiaryCode,
                FullName = b.User.FullName,
                Gender = b.Gender.ToString(),
                Village = b.Village,
                District = b.District,
                State = b.State,
                SchemeCode = b.Family.RationScheme.SchemeCode,
                ShopName = b.Family.RationShop.ShopName,
                FamilySize = b.Family.Members.Count,
                AadhaarStatus = b.AadhaarVerification?.Status.ToString() ?? "NotVerified",
                PassbookStatus = b.PassbookVerification?.VerificationStatus.ToString() ?? "NotVerified",
                IsActive = b.IsActive,
                IsBlocked = b.IsBlocked
            }).ToList()
        };
    }

    private async Task<PagedResultDto<FamilyMemberRowDto>> GetFamilyMembersAsync(string? search, int page, int pageSize)
    {
        var query = db.FamilyMembers.Include(m => m.Family).AsQueryable();
        if (!string.IsNullOrWhiteSpace(search))
        {
            var term = search.Trim().ToLowerInvariant();
            query = query.Where(m => m.FullName.ToLower().Contains(term) || m.Family.FamilyCode.ToLower().Contains(term));
        }

        var totalCount = await query.CountAsync();
        var items = await query.OrderBy(m => m.Id).Skip((page - 1) * pageSize).Take(pageSize).ToListAsync();

        return new PagedResultDto<FamilyMemberRowDto>
        {
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
            Items = items.Select(m => new FamilyMemberRowDto
            {
                Id = m.Id,
                FamilyCode = m.Family.FamilyCode,
                FullName = m.FullName,
                Age = m.Age,
                Relationship = m.Relationship.ToString(),
                Eligibility = m.Eligibility.ToString()
            }).ToList()
        };
    }

    private async Task<PagedResultDto<TokenRowDto>> GetTokensAsync(string? search, int page, int pageSize)
    {
        var query = db.Tokens.Include(t => t.User).ThenInclude(u => u.Beneficiary).Include(t => t.RationShop).Include(t => t.TimeSlot).AsQueryable();
        if (!string.IsNullOrWhiteSpace(search))
        {
            var term = search.Trim().ToLowerInvariant();
            query = query.Where(t => t.TokenNumber.ToLower().Contains(term));
        }

        var totalCount = await query.CountAsync();
        var items = await query.OrderByDescending(t => t.Id).Skip((page - 1) * pageSize).Take(pageSize).ToListAsync();

        return new PagedResultDto<TokenRowDto>
        {
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
            Items = items.Select(t => new TokenRowDto
            {
                Id = t.Id,
                TokenNumber = t.TokenNumber,
                BeneficiaryCode = t.User.Beneficiary?.BeneficiaryCode ?? "—",
                ShopName = t.RationShop.ShopName,
                SlotDate = t.TimeSlot.SlotDate.ToString("yyyy-MM-dd"),
                Status = t.Status.ToString(),
                QrCodeValue = t.QRCodeValue
            }).ToList()
        };
    }

    private async Task<PagedResultDto<CollectionRowDto>> GetCollectionsAsync(string? search, int page, int pageSize)
    {
        var query = db.RationCollections.Include(c => c.Beneficiary).Include(c => c.RationShop).Include(c => c.Items).AsQueryable();
        if (!string.IsNullOrWhiteSpace(search))
        {
            var term = search.Trim().ToLowerInvariant();
            query = query.Where(c => c.CollectionCode.ToLower().Contains(term));
        }

        var totalCount = await query.CountAsync();
        var items = await query.OrderByDescending(c => c.CollectedAt).Skip((page - 1) * pageSize).Take(pageSize).ToListAsync();

        return new PagedResultDto<CollectionRowDto>
        {
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
            Items = items.Select(c => new CollectionRowDto
            {
                Id = c.Id,
                CollectionCode = c.CollectionCode,
                BeneficiaryCode = c.Beneficiary.BeneficiaryCode,
                ShopName = c.RationShop.ShopName,
                CollectedAt = c.CollectedAt.ToString("yyyy-MM-dd HH:mm"),
                TotalQuantityKg = c.Items.Sum(i => i.Quantity)
            }).ToList()
        };
    }

    private async Task<PagedResultDto<InventoryRowDto>> GetInventoryAsync(int page, int pageSize)
    {
        var query = db.Inventory.Include(i => i.RationShop).AsQueryable();
        var totalCount = await query.CountAsync();
        var items = await query.OrderBy(i => i.RationShopId).Skip((page - 1) * pageSize).Take(pageSize).ToListAsync();

        return new PagedResultDto<InventoryRowDto>
        {
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
            Items = items.Select(i => new InventoryRowDto
            {
                Id = i.Id,
                ShopName = i.RationShop.ShopName,
                RationType = i.RationType.ToString(),
                Available = i.AvailableQuantity,
                Allocated = i.AllocatedQuantity,
                MinimumStockLevel = i.MinimumStockLevel
            }).ToList()
        };
    }

    private async Task<PagedResultDto<AIInsightRowDto>> GetAIInsightsAsync(int page, int pageSize)
    {
        var query = db.AIInsights.AsQueryable();
        var totalCount = await query.CountAsync();
        var items = await query.OrderByDescending(i => i.CreatedAt).Skip((page - 1) * pageSize).Take(pageSize).ToListAsync();

        return new PagedResultDto<AIInsightRowDto>
        {
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
            Items = items.Select(i => new AIInsightRowDto
            {
                Id = i.Id,
                EntityType = i.EntityType,
                EntityId = i.EntityId,
                InsightType = i.InsightType,
                RiskLevel = i.RiskLevel.ToString(),
                Score = i.Score,
                Explanation = i.Explanation,
                CreatedAt = i.CreatedAt.ToString("yyyy-MM-dd HH:mm")
            }).ToList()
        };
    }

    private async Task<PagedResultDto<VerificationAuditLogDto>> GetAuditLogsAsync(int page, int pageSize)
    {
        var query = db.VerificationAuditLogs.AsQueryable();
        var totalCount = await query.CountAsync();
        var items = await query.OrderByDescending(l => l.Timestamp).Skip((page - 1) * pageSize).Take(pageSize).ToListAsync();

        return new PagedResultDto<VerificationAuditLogDto>
        {
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
            Items = items.Select(l => new VerificationAuditLogDto
            {
                Id = l.Id,
                VerificationReference = l.VerificationReference,
                Action = l.Action.ToString(),
                VerificationMethod = l.VerificationMethod,
                TokenNumber = l.TokenNumber,
                BeneficiaryId = l.BeneficiaryId,
                ShopId = l.ShopId,
                OperatorId = l.OperatorId,
                Status = l.Status,
                Reason = l.Reason,
                Timestamp = l.Timestamp.ToString("yyyy-MM-dd HH:mm:ss")
            }).ToList()
        };
    }
}
