using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Inventory;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/inventory")]
[Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class InventoryController(IInventoryService inventoryService) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<ApiResponse<IReadOnlyList<InventoryDto>>>> GetInventory([FromQuery] int? shopId)
    {
        var result = await inventoryService.GetInventoryAsync(shopId);
        return Ok(ApiResponse<IReadOnlyList<InventoryDto>>.Ok(result));
    }

    [HttpPost]
    public async Task<ActionResult<ApiResponse<InventoryDto>>> CreateInventory(CreateInventoryRequestDto request)
    {
        var result = await inventoryService.CreateInventoryAsync(request);
        return Ok(ApiResponse<InventoryDto>.Ok(result, "Inventory record created"));
    }

    [HttpPut("{id:int}")]
    public async Task<ActionResult<ApiResponse<InventoryDto>>> UpdateInventory(int id, UpdateInventoryRequestDto request)
    {
        var result = await inventoryService.UpdateInventoryAsync(id, request);
        return Ok(ApiResponse<InventoryDto>.Ok(result, "Inventory updated"));
    }
}
