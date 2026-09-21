using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Shop;

namespace SmartRation.Api.Controllers;

// Read-only shop directory — rural users need it to pick a shop when
// booking, and government officials need it for the shop management
// screen. Creating/editing shops is out of scope for this phase.
[ApiController]
[Route("api/shops")]
[Authorize]
public class ShopsController(SmartRationDbContext db) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<ApiResponse<List<RationShopDto>>>> GetShops()
    {
        var shops = await db.RationShops
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

        return Ok(ApiResponse<List<RationShopDto>>.Ok(shops));
    }
}
