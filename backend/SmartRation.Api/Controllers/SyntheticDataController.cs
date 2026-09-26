using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Admin;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

// Development/demo tooling only — lists the synthetic beneficiary dataset
// with search/filter/pagination. Never exposed to RuralUser or ShopOwner.
// Same query as the database viewer (AdminDatabaseBrowserService), plus the extra filters.
[ApiController]
[Route("api/admin/synthetic-data")]
[Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class SyntheticDataController(IAdminDatabaseBrowserService browser) : ControllerBase
{
    [HttpGet("beneficiaries")]
    public async Task<ActionResult<ApiResponse<PagedResultDto<SyntheticBeneficiaryRowDto>>>> GetBeneficiaries(
        [FromQuery] string? search,
        [FromQuery] string? district,
        [FromQuery] string? aadhaarStatus,
        [FromQuery] string? passbookStatus,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20)
    {
        var filter = new BeneficiaryFilter(district, aadhaarStatus, passbookStatus, SearchMobile: true);
        var result = await browser.GetBeneficiariesAsync(search, Math.Max(1, page), Math.Clamp(pageSize, 1, 100), filter);
        return Ok(ApiResponse<PagedResultDto<SyntheticBeneficiaryRowDto>>.Ok(result));
    }
}
