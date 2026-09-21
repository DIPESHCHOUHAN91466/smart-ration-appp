using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Inventory;

public class UpdateInventoryRequestDto
{
    [Range(0, double.MaxValue)]
    public decimal AvailableQuantity { get; set; }

    [Range(0, double.MaxValue)]
    public decimal MinimumStockLevel { get; set; }
}
