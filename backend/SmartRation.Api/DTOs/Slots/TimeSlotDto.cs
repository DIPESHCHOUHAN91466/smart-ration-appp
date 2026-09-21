namespace SmartRation.Api.DTOs.Slots;

public class TimeSlotDto
{
    public int Id { get; set; }

    public int RationShopId { get; set; }

    public DateTime SlotDate { get; set; }

    public TimeSpan StartTime { get; set; }

    public TimeSpan EndTime { get; set; }

    public int Capacity { get; set; }

    public int BookedCount { get; set; }

    // Available | Limited | Full
    public string Status { get; set; } = string.Empty;
}
