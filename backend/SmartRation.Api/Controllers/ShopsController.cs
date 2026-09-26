using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Map;
using SmartRation.Api.DTOs.Shop;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Controllers;

// Read-only shop directory — rural users need it to pick a shop when
// booking, and government officials need it for the shop management
// screen. Creating/editing shops is out of scope for this phase.
[ApiController]
[Route("api/shops")]
[Authorize]
public class ShopsController(IShopDirectoryService directory, IMapService mapService) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<ApiResponse<List<RationShopDto>>>> GetShops()
    {
        return Ok(ApiResponse<List<RationShopDto>>.Ok(await directory.GetActiveShopsAsync()));
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
