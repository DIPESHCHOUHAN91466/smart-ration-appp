using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Shop;

namespace SmartRation.Api.Services;

// The read-only list of active shops (citizens pick one when booking; officials manage them).
public interface IShopDirectoryService
{
    Task<List<RationShopDto>> GetActiveShopsAsync();
}

public class ShopDirectoryService(SmartRationDbContext db) : IShopDirectoryService
{
    public Task<List<RationShopDto>> GetActiveShopsAsync() =>
        db.RationShops
            .Where(s => s.IsActive)
            .OrderBy(s => s.ShopName)
            .Select(s => new RationShopDto
            {
                Id = s.Id,
                ShopName = s.ShopName,
                ShopCode = s.ShopCode,
                Address = s.Address,
                District = s.District,
                State = s.State,
                IsActive = s.IsActive
            })
            .ToListAsync();
}
