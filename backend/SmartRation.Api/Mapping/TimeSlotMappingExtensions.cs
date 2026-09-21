using SmartRation.Api.DTOs.Slots;
using SmartRation.Api.Models;

namespace SmartRation.Api.Mapping;

public static class TimeSlotMappingExtensions
{
    public static TimeSlotDto ToDto(this TimeSlot slot)
    {
        var remaining = slot.Capacity - slot.BookedCount;

        var status = remaining <= 0
            ? "Full"
            : slot.Capacity > 1 && remaining <= Math.Max(1, slot.Capacity / 5)
                ? "Limited"
                : "Available";

        return new TimeSlotDto
        {
            Id = slot.Id,
            RationShopId = slot.RationShopId,
            SlotDate = slot.SlotDate,
            StartTime = slot.StartTime,
            EndTime = slot.EndTime,
            Capacity = slot.Capacity,
            BookedCount = slot.BookedCount,
            Status = status
        };
    }
}
