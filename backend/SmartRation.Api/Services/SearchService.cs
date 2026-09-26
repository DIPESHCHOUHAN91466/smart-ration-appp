using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Admin;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

// The dashboard's top search box (SearchController). Results and their target routes are scoped
// by role on the server: a RuralUser sees only their own beneficiary and tokens, a ShopOwner only
// their own shop's, and only officials/admins see shops. Security-critical: see SearchServiceTests.
public interface ISearchService
{
    Task<List<SearchResultDto>> SearchAsync(string? q);
}

public class SearchService(SmartRationDbContext db, ICurrentUserService currentUser) : ISearchService
{
    public const int MaxPerType = 5;

    public async Task<List<SearchResultDto>> SearchAsync(string? q)
    {
        var results = new List<SearchResultDto>();
        if (string.IsNullOrWhiteSpace(q) || q.Trim().Length < 2)
        {
            return results;
        }

        var term = q.Trim().ToLowerInvariant();
        var beneficiaryQuery = db.Beneficiaries.AsQueryable();
        var tokenQuery = db.Tokens.AsQueryable();

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
            case UserRole.GovernmentOfficial:
            case UserRole.Admin:
                break;
            default:
                return results; // an unknown role sees nothing rather than everything
        }

        results.AddRange(await beneficiaryQuery
            .Where(b => b.BeneficiaryCode.ToLower().Contains(term) || b.User.FullName.ToLower().Contains(term))
            .OrderBy(b => b.Id)
            .Take(MaxPerType)
            .Select(b => new SearchResultDto { Type = "Beneficiary", Title = b.User.FullName, Subtitle = b.BeneficiaryCode, Path = $"/beneficiary/{b.Id}" })
            .ToListAsync());

        var isRural = currentUser.Role == UserRole.RuralUser;
        results.AddRange(await tokenQuery
            .Where(t => t.TokenNumber.ToLower().Contains(term))
            .OrderByDescending(t => t.Id)
            .Take(MaxPerType)
            .Select(t => new SearchResultDto { Type = "Token", Title = t.TokenNumber, Subtitle = t.RationShop.ShopName, Path = isRural ? $"/rural/token/{t.Id}" : "/gov/bookings" })
            .ToListAsync());

        if (currentUser.Role is UserRole.GovernmentOfficial or UserRole.Admin)
        {
            results.AddRange(await db.RationShops
                .Where(s => s.ShopName.ToLower().Contains(term) || s.ShopCode.ToLower().Contains(term))
                .OrderBy(s => s.Id)
                .Take(MaxPerType)
                .Select(s => new SearchResultDto { Type = "Shop", Title = s.ShopName, Subtitle = s.ShopCode, Path = "/gov/shops" })
                .ToListAsync());
        }

        return results;
    }
}
