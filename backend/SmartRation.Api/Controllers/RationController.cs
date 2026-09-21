using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/ration")]
[Authorize]
public class RationController(SmartRationDbContext db, IBookingService bookingService) : ControllerBase
{
    [HttpGet("items")]
    public async Task<ActionResult<ApiResponse<List<RationItemDto>>>> GetItems()
    {
        var items = await db.RationItems
            .Where(r => r.IsActive)
            .Select(r => new RationItemDto
            {
                Id = r.Id,
                RationType = r.RationType.ToString(),
                Name = r.Name,
                VernacularName = r.VernacularName,
                Unit = r.Unit,
                StandardQuotaPerBooking = r.StandardQuotaPerBooking
            })
            .ToListAsync();

        return Ok(ApiResponse<List<RationItemDto>>.Ok(items));
    }

    [HttpPost("bookings")]
    [Authorize(Roles = nameof(UserRole.RuralUser))]
    public async Task<ActionResult<ApiResponse<TokenDto>>> CreateBooking(CreateBookingRequestDto request)
    {
        var result = await bookingService.CreateBookingAsync(request);
        return Ok(ApiResponse<TokenDto>.Ok(result, "Booking created and token generated"));
    }

    [HttpGet("bookings")]
    public async Task<ActionResult<ApiResponse<IReadOnlyList<TokenDto>>>> GetBookings()
    {
        var result = await bookingService.GetBookingsAsync();
        return Ok(ApiResponse<IReadOnlyList<TokenDto>>.Ok(result));
    }

    [HttpGet("bookings/{id:int}")]
    public async Task<ActionResult<ApiResponse<TokenDto>>> GetBooking(int id)
    {
        var result = await bookingService.GetBookingByIdAsync(id);
        return Ok(ApiResponse<TokenDto>.Ok(result));
    }

    [HttpPut("bookings/{id:int}")]
    [Authorize(Roles = nameof(UserRole.RuralUser))]
    public async Task<ActionResult<ApiResponse<TokenDto>>> RescheduleBooking(int id, RescheduleBookingRequestDto request)
    {
        var result = await bookingService.RescheduleBookingAsync(id, request.TimeSlotId);
        return Ok(ApiResponse<TokenDto>.Ok(result, "Booking rescheduled"));
    }

    [HttpDelete("bookings/{id:int}")]
    public async Task<ActionResult<ApiResponse<object?>>> CancelBooking(int id)
    {
        await bookingService.CancelBookingAsync(id);
        return Ok(ApiResponse.Ok("Booking cancelled"));
    }
}
