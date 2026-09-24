using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Admin;
using SmartRation.Api.Models;

namespace SmartRation.Api.Controllers;

// Development/demo tooling only — lists the synthetic beneficiary dataset
// with search/filter/pagination. Never exposed to RuralUser or ShopOwner.
[ApiController]
[Route("api/admin/synthetic-data")]
[Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class SyntheticDataController(SmartRationDbContext db) : ControllerBase
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
            query = query.Where(b =>
                b.BeneficiaryCode.ToLower().Contains(term) ||
                b.User.FullName.ToLower().Contains(term) ||
                b.User.MobileNumber.Contains(term));
        }

        if (!string.IsNullOrWhiteSpace(district))
        {
            query = query.Where(b => b.District == district);
        }

        if (!string.IsNullOrWhiteSpace(aadhaarStatus) && Enum.TryParse<AadhaarVerificationStatus>(aadhaarStatus, true, out var aStatus))
        {
            query = query.Where(b => b.AadhaarVerification != null && b.AadhaarVerification.Status == aStatus);
        }

        if (!string.IsNullOrWhiteSpace(passbookStatus) && Enum.TryParse<PassbookVerificationStatus>(passbookStatus, true, out var pStatus))
        {
            query = query.Where(b => b.PassbookVerification != null && b.PassbookVerification.VerificationStatus == pStatus);
        }

        var totalCount = await query.CountAsync();

        page = Math.Max(1, page);
        pageSize = Math.Clamp(pageSize, 1, 100);

        var pageItems = await query
            .OrderBy(b => b.Id)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

        var rows = pageItems.Select(b => new SyntheticBeneficiaryRowDto
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
        }).ToList();

        return Ok(ApiResponse<PagedResultDto<SyntheticBeneficiaryRowDto>>.Ok(new PagedResultDto<SyntheticBeneficiaryRowDto>
        {
            Items = rows,
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize
        }));
    }
}
