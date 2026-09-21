using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Ration;

public class RescheduleBookingRequestDto
{
    [Required]
    public int TimeSlotId { get; set; }
}
