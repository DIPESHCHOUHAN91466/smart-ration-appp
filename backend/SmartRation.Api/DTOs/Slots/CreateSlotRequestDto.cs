using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Slots;

public class CreateSlotRequestDto
{
    [Required]
    public int RationShopId { get; set; }

    [Required]
    public DateTime SlotDate { get; set; }

    [Required]
    public TimeSpan StartTime { get; set; }

    [Required]
    public TimeSpan EndTime { get; set; }

    [Range(1, 500)]
    public int Capacity { get; set; } = 1;
}
