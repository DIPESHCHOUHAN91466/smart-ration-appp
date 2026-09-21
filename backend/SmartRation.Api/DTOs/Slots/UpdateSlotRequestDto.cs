using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Slots;

public class UpdateSlotRequestDto
{
    [Range(1, 500)]
    public int Capacity { get; set; }
}
