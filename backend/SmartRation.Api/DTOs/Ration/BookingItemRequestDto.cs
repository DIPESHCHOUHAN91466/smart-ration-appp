using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Ration;

public class BookingItemRequestDto
{
    [Required]
    public string RationType { get; set; } = string.Empty;

    [Range(0.01, 1000)]
    public decimal Quantity { get; set; }
}
