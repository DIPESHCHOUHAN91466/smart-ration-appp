using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Inventory;

public class CreateInventoryRequestDto
{
    [Required]
    public int RationShopId { get; set; }

    [Required]
    public string RationType { get; set; } = string.Empty;

    [Range(0, double.MaxValue)]
    public decimal AvailableQuantity { get; set; }

    [Range(0, double.MaxValue)]
    public decimal MinimumStockLevel { get; set; }
}
