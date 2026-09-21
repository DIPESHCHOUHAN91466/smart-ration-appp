using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Government;
using SmartRation.Api.DTOs.Users;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/admin")]
[Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class AdminController(IGovernmentService governmentService, SmartRationDbContext db) : ControllerBase
{
    [HttpGet("dashboard")]
    public async Task<ActionResult<ApiResponse<GovernmentDashboardDto>>> GetDashboard()
    {
        var result = await governmentService.GetDashboardAsync();
        return Ok(ApiResponse<GovernmentDashboardDto>.Ok(result));
    }

    [HttpGet("statistics")]
    public async Task<ActionResult<ApiResponse<StatisticsDto>>> GetStatistics([FromQuery] DateTime? fromDate, [FromQuery] DateTime? toDate)
    {
        var result = await governmentService.GetStatisticsAsync(fromDate, toDate);
        return Ok(ApiResponse<StatisticsDto>.Ok(result));
    }

    [HttpGet("reports")]
    public async Task<ActionResult<ApiResponse<IReadOnlyList<ReportSummaryDto>>>> GetReports([FromQuery] DateTime? fromDate, [FromQuery] DateTime? toDate)
    {
        var result = await governmentService.GetReportsAsync(fromDate, toDate);
        return Ok(ApiResponse<IReadOnlyList<ReportSummaryDto>>.Ok(result));
    }

    [HttpGet("users")]
    public async Task<ActionResult<ApiResponse<List<UserSummaryDto>>>> GetUsers([FromQuery] string? role)
    {
        var query = db.Users.AsQueryable();

        if (!string.IsNullOrWhiteSpace(role))
        {
            if (!Enum.TryParse<UserRole>(role, ignoreCase: true, out var parsedRole))
            {
                throw new BadRequestException($"Unknown role '{role}'.");
            }

            query = query.Where(u => u.Role == parsedRole);
        }

        var users = await query.OrderBy(u => u.FullName).ToListAsync();
        return Ok(ApiResponse<List<UserSummaryDto>>.Ok(users.Select(u => u.ToSummaryDto()).ToList()));
    }
}
