namespace SmartRation.Api.Models;

public class TimeSlot
{
    public int Id { get; set; }

    public int RationShopId { get; set; }

    public RationShop RationShop { get; set; } = null!;

    public DateTime SlotDate { get; set; }

    public TimeSpan StartTime { get; set; }

    public TimeSpan EndTime { get; set; }

    // Single-person booking as requested
    public int Capacity { get; set; } = 1;

    public int BookedCount { get; set; } = 0;

    public bool IsAvailable =>
        BookedCount < Capacity;
}