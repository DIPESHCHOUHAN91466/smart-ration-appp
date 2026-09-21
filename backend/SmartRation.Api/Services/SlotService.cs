using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Slots;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public class SlotService(SmartRationDbContext db, ICurrentUserService currentUser) : ISlotService
{
    public async Task<IReadOnlyList<TimeSlotDto>> GetSlotsAsync(int shopId, DateTime date)
    {
        var shopExists = await db.RationShops.AnyAsync(s => s.Id == shopId);
        if (!shopExists)
        {
            throw new NotFoundException("Ration shop not found.");
        }

        // SQLite can't ORDER BY a TimeSpan column, so sort client-side after materializing.
        var slots = await db.TimeSlots
            .Where(s => s.RationShopId == shopId && s.SlotDate.Date == date.Date)
            .ToListAsync();

        return slots.OrderBy(s => s.StartTime).Select(s => s.ToDto()).ToList();
    }

    public async Task<TimeSlotDto> CreateSlotAsync(CreateSlotRequestDto request)
    {
        var shop = await db.RationShops.FirstOrDefaultAsync(s => s.Id == request.RationShopId)
            ?? throw new NotFoundException("Ration shop not found.");

        EnsureCanManage(shop.Id);

        if (request.EndTime <= request.StartTime)
        {
            throw new BadRequestException("End time must be after start time.");
        }

        var overlaps = await db.TimeSlots.AnyAsync(s =>
            s.RationShopId == shop.Id &&
            s.SlotDate.Date == request.SlotDate.Date &&
            request.StartTime < s.EndTime && s.StartTime < request.EndTime);

        if (overlaps)
        {
            throw new ConflictException("This time slot overlaps with an existing slot for this shop.");
        }

        var slot = new TimeSlot
        {
            RationShopId = shop.Id,
            SlotDate = request.SlotDate.Date,
            StartTime = request.StartTime,
            EndTime = request.EndTime,
            Capacity = request.Capacity,
            BookedCount = 0
        };

        db.TimeSlots.Add(slot);
        await db.SaveChangesAsync();

        return slot.ToDto();
    }

    public async Task<TimeSlotDto> UpdateSlotAsync(int id, UpdateSlotRequestDto request)
    {
        var slot = await db.TimeSlots.FirstOrDefaultAsync(s => s.Id == id)
            ?? throw new NotFoundException("Time slot not found.");

        EnsureCanManage(slot.RationShopId);

        if (request.Capacity < slot.BookedCount)
        {
            throw new BadRequestException($"Capacity cannot be less than the {slot.BookedCount} beneficiaries already booked into this slot.");
        }

        slot.Capacity = request.Capacity;
        await db.SaveChangesAsync();

        return slot.ToDto();
    }

    private void EnsureCanManage(int shopId)
    {
        var allowed = currentUser.Role switch
        {
            UserRole.ShopOwner => currentUser.RationShopId == shopId,
            UserRole.GovernmentOfficial or UserRole.Admin => true,
            _ => false
        };

        if (!allowed)
        {
            throw new ForbiddenException("You do not have permission to manage time slots for this shop.");
        }
    }
}
