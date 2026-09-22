using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/audit")]
[Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class AuditController(SmartRationDbContext db) : ControllerBase
{
    [HttpGet("verification")]
    public async Task<ActionResult<ApiResponse<List<VerificationAuditLogDto>>>> GetVerificationAudit(
        [FromQuery] int? shopId,
        [FromQuery] int? beneficiaryId,
        [FromQuery] string? status,
        [FromQuery] int take = 100)
    {
        var query = db.VerificationAuditLogs.AsQueryable();

        if (shopId.HasValue) query = query.Where(l => l.ShopId == shopId);
        if (beneficiaryId.HasValue) query = query.Where(l => l.BeneficiaryId == beneficiaryId);
        if (!string.IsNullOrWhiteSpace(status)) query = query.Where(l => l.Status == status);

        var logs = await query
            .OrderByDescending(l => l.Timestamp)
            .Take(Math.Clamp(take, 1, 500))
            .ToListAsync();

        var result = logs.Select(l => new VerificationAuditLogDto
        {
            Id = l.Id,
            VerificationReference = l.VerificationReference,
            TokenNumber = l.TokenNumber,
            BeneficiaryId = l.BeneficiaryId,
            ShopId = l.ShopId,
            Action = l.Action.ToString(),
            VerificationMethod = l.VerificationMethod,
            Status = l.Status,
            Reason = l.Reason,
            OperatorId = l.OperatorId,
            Timestamp = l.Timestamp.ToString("yyyy-MM-dd HH:mm:ss")
        }).ToList();

        return Ok(ApiResponse<List<VerificationAuditLogDto>>.Ok(result));
    }
}
