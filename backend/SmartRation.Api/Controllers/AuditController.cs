using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Controllers;

// Verification audit trail for officials. Query: VerificationAuditService.
[ApiController]
[Route("api/audit")]
[Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class AuditController(IVerificationAuditService audit) : ControllerBase
{
    [HttpGet("verification")]
    public async Task<ActionResult<ApiResponse<List<VerificationAuditLogDto>>>> GetVerificationAudit(
        [FromQuery] int? shopId,
        [FromQuery] int? beneficiaryId,
        [FromQuery] string? status,
        [FromQuery] int take = 100) =>
        Ok(ApiResponse<List<VerificationAuditLogDto>>.Ok(await audit.QueryAsync(shopId, beneficiaryId, status, take)));
}
