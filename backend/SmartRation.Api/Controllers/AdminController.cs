using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Government;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/admin")]
[Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class AdminController(IGovernmentService governmentService) : ControllerBase
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
}
