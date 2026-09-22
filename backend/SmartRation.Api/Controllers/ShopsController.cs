using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Map;
using SmartRation.Api.DTOs.Shop;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Controllers;

// Read-only shop directory — rural users need it to pick a shop when
// booking, and government officials need it for the shop management
// screen. Creating/editing shops is out of scope for this phase.
[ApiController]
[Route("api/shops")]
[Authorize]
public class ShopsController(SmartRationDbContext db, IMapService mapService) : ControllerBase
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

    // DEMO MAP DATA — see MapService for what's real vs synthetic.
    [HttpGet("map")]
    [Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<List<ShopMapMarkerDto>>>> GetMap(
        [FromQuery] string? state, [FromQuery] string? district, [FromQuery] string? taluka,
        [FromQuery] string? village, [FromQuery] string? schemeCode, [FromQuery] string? inventoryStatus)
    {
        var markers = await mapService.GetShopMarkersAsync(state, district, taluka, village, schemeCode, inventoryStatus);
        return Ok(ApiResponse<List<ShopMapMarkerDto>>.Ok(markers));
    }

    [HttpGet("{id:int}/location")]
    [Authorize(Roles = $"{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<ShopMapDetailDto>>> GetLocation(int id)
    {
        var detail = await mapService.GetShopDetailAsync(id);
        return Ok(ApiResponse<ShopMapDetailDto>.Ok(detail));
    }
}
