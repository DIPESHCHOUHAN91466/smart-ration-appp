using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Inventory;

public class StockMovementRequestDto
{
    // Strictly positive: zero or negative movements are rejected by model validation.
    [Range(0.01, 1_000_000)]
    public decimal Quantity { get; set; }

    // Delivery challan / reference number. Never personal data.
    [MaxLength(64)]
    [RegularExpression(@"^[A-Za-z0-9\-/_. ]*$", ErrorMessage = "Reference may only contain letters, numbers and - / _ .")]
    public string? Reference { get; set; }

    [MaxLength(256)]
    public string? Note { get; set; }
}
