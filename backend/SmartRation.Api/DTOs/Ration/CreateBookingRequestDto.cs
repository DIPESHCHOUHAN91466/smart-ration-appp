using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Ration;

public class CreateBookingRequestDto
{
    [Required]
    public int RationShopId { get; set; }

    [Required]
    public int TimeSlotId { get; set; }

    [Required, MinLength(1, ErrorMessage = "Select at least one ration item.")]
    public List<BookingItemRequestDto> Items { get; set; } = [];
}
