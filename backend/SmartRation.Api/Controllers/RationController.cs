using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/ration")]
[Authorize]
public class RationController(
    SmartRationDbContext db,
    IBookingService bookingService,
    IEntitlementService entitlementService,
    ICurrentUserService currentUser) : ControllerBase
{
    // shopId (optional): includes each item's current available shop stock —
    // read-only, never the shop's minimum-stock-level or other management fields.
    // For a RuralUser caller, also includes their own family's remaining
    // entitlement per item this month (scheme/family-size driven, never a
    // hardcoded universal quota).
    [HttpGet("items")]
    public async Task<ActionResult<ApiResponse<List<RationItemDto>>>> GetItems([FromQuery] int? shopId)
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

        if (shopId.HasValue)
        {
            var stock = await db.Inventory
                .Where(i => i.RationShopId == shopId.Value)
                .ToDictionaryAsync(i => i.RationType.ToString(), i => i.AvailableQuantity);

            foreach (var item in items)
            {
                if (stock.TryGetValue(item.RationType, out var available))
                {
                    item.AvailableQuantity = available;
                }
            }
        }

        if (currentUser.Role == UserRole.RuralUser)
        {
            var familyId = await db.Beneficiaries
                .Where(b => b.UserId == currentUser.UserId)
                .Select(b => (int?)b.FamilyId)
                .FirstOrDefaultAsync();

            if (familyId.HasValue)
            {
                var entitlement = await entitlementService.GetEntitlementAsync(familyId.Value);
                var remaining = entitlement.Items.ToDictionary(i => i.RationType, i => i.Remaining);

                foreach (var item in items)
                {
                    if (remaining.TryGetValue(item.RationType, out var eligible))
                    {
                        item.EligibleQuantity = eligible;
                    }
                }
            }
        }

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
