using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Admin;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

// Backs the dashboard's top search box. Results and their target routes are
// scoped by role server-side — a ShopOwner only ever sees their own shop's
// beneficiaries and tokens, never another shop's data.
[ApiController]
[Route("api/search")]
[Authorize]
public class SearchController(SmartRationDbContext db, ICurrentUserService currentUser) : ControllerBase
{
    private const int MaxPerType = 5;

    [HttpGet]
    public async Task<ActionResult<ApiResponse<List<SearchResultDto>>>> Search([FromQuery] string? q)
    {
        var results = new List<SearchResultDto>();
        if (string.IsNullOrWhiteSpace(q) || q.Trim().Length < 2)
        {
            return Ok(ApiResponse<List<SearchResultDto>>.Ok(results));
        }

        var term = q.Trim().ToLowerInvariant();

        var beneficiaryQuery = db.Beneficiaries.Include(b => b.User).Include(b => b.Family).AsQueryable();
        var tokenQuery = db.Tokens.Include(t => t.User).Include(t => t.RationShop).AsQueryable();

        switch (currentUser.Role)
        {
            case UserRole.RuralUser:
                beneficiaryQuery = beneficiaryQuery.Where(b => b.UserId == currentUser.UserId);
                tokenQuery = tokenQuery.Where(t => t.UserId == currentUser.UserId);
                break;
            case UserRole.ShopOwner:
                beneficiaryQuery = beneficiaryQuery.Where(b => b.Family.RationShopId == currentUser.RationShopId);
                tokenQuery = tokenQuery.Where(t => t.RationShopId == currentUser.RationShopId);
                break;
        }

        var beneficiaries = await beneficiaryQuery
            .Where(b => b.BeneficiaryCode.ToLower().Contains(term) || b.User.FullName.ToLower().Contains(term))
            .OrderBy(b => b.Id)
            .Take(MaxPerType)
            .Select(b => new SearchResultDto
            {
                Type = "Beneficiary",
                Title = b.User.FullName,
                Subtitle = b.BeneficiaryCode,
                Path = $"/beneficiary/{b.Id}"
            })
            .ToListAsync();
        results.AddRange(beneficiaries);

        var tokens = await tokenQuery
            .Where(t => t.TokenNumber.ToLower().Contains(term))
            .OrderByDescending(t => t.Id)
            .Take(MaxPerType)
            .Select(t => new SearchResultDto
            {
                Type = "Token",
                Title = t.TokenNumber,
                Subtitle = t.RationShop.ShopName,
                Path = currentUser.Role == UserRole.RuralUser ? $"/rural/token/{t.Id}" : "/gov/bookings"
            })
            .ToListAsync();
        results.AddRange(tokens);

        if (currentUser.Role is UserRole.GovernmentOfficial or UserRole.Admin)
        {
            var shops = await db.RationShops
                .Where(s => s.ShopName.ToLower().Contains(term) || s.ShopCode.ToLower().Contains(term))
                .OrderBy(s => s.Id)
                .Take(MaxPerType)
                .Select(s => new SearchResultDto
                {
                    Type = "Shop",
                    Title = s.ShopName,
                    Subtitle = s.ShopCode,
                    Path = "/gov/shops"
                })
                .ToListAsync();
            results.AddRange(shops);
        }

        return Ok(ApiResponse<List<SearchResultDto>>.Ok(results));
    }
}
