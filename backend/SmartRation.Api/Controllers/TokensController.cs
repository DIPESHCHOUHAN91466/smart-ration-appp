using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/tokens")]
[Authorize]
public class TokensController(IBookingService bookingService) : ControllerBase
{
    // Alias for POST /api/ration/bookings — generating a token IS creating a
    // booking in this system, so both routes share the same service call.
    [HttpPost("generate")]
    [Authorize(Roles = nameof(UserRole.RuralUser))]
    public async Task<ActionResult<ApiResponse<TokenDto>>> Generate(CreateBookingRequestDto request)
    {
        var result = await bookingService.CreateBookingAsync(request);
        return Ok(ApiResponse<TokenDto>.Ok(result, "Token generated"));
    }

    [HttpGet("{id:int}")]
    public async Task<ActionResult<ApiResponse<TokenDto>>> GetById(int id)
    {
        var result = await bookingService.GetBookingByIdAsync(id);
        return Ok(ApiResponse<TokenDto>.Ok(result));
    }

    [HttpGet("today")]
    [Authorize(Roles = nameof(UserRole.ShopOwner))]
    public async Task<ActionResult<ApiResponse<IReadOnlyList<TokenDto>>>> Today()
    {
        var result = await bookingService.GetTodayQueueForCurrentShopAsync();
        return Ok(ApiResponse<IReadOnlyList<TokenDto>>.Ok(result));
    }
}
