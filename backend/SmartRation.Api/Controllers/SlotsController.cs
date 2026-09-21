using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Slots;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/slots")]
[Authorize]
public class SlotsController(ISlotService slotService) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<ApiResponse<IReadOnlyList<TimeSlotDto>>>> GetSlots([FromQuery] int shopId, [FromQuery] DateTime date)
    {
        var result = await slotService.GetSlotsAsync(shopId, date);
        return Ok(ApiResponse<IReadOnlyList<TimeSlotDto>>.Ok(result));
    }

    [HttpPost]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<TimeSlotDto>>> CreateSlot(CreateSlotRequestDto request)
    {
        var result = await slotService.CreateSlotAsync(request);
        return Ok(ApiResponse<TimeSlotDto>.Ok(result, "Time slot created"));
    }

    [HttpPut("{id:int}")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<TimeSlotDto>>> UpdateSlot(int id, UpdateSlotRequestDto request)
    {
        var result = await slotService.UpdateSlotAsync(id, request);
        return Ok(ApiResponse<TimeSlotDto>.Ok(result, "Time slot updated"));
    }
}
