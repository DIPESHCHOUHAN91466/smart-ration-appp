using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.DTOs.Shop;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/shop")]
[Authorize(Roles = nameof(UserRole.ShopOwner))]
public class ShopController(IShopService shopService, IBookingService bookingService) : ControllerBase
{
    [HttpGet("dashboard")]
    public async Task<ActionResult<ApiResponse<ShopDashboardDto>>> GetDashboard()
    {
        var result = await shopService.GetDashboardAsync();
        return Ok(ApiResponse<ShopDashboardDto>.Ok(result));
    }

    [HttpGet("queue")]
    public async Task<ActionResult<ApiResponse<IReadOnlyList<TokenDto>>>> GetQueue()
    {
        var result = await bookingService.GetTodayQueueForCurrentShopAsync();
        return Ok(ApiResponse<IReadOnlyList<TokenDto>>.Ok(result));
    }

    [HttpPost("collection/complete")]
    public async Task<ActionResult<ApiResponse<TokenDto>>> CompleteCollection(
        CompleteCollectionRequestDto request,
        [FromHeader(Name = "Idempotency-Key")] string? idempotencyKey)
    {
        var result = await shopService.CompleteCollectionAsync(request.TokenId, idempotencyKey is { Length: > 0 and <= 64 } ? idempotencyKey : null);
        return Ok(ApiResponse<TokenDto>.Ok(result, "Collection marked complete"));
    }
}
