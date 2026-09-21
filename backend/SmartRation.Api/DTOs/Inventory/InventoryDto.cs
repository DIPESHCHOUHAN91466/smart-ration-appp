namespace SmartRation.Api.DTOs.Inventory;

public class InventoryDto
{
    public int Id { get; set; }

    public int RationShopId { get; set; }

    public string RationType { get; set; } = string.Empty;

    public decimal AvailableQuantity { get; set; }

    public decimal AllocatedQuantity { get; set; }

    public decimal MinimumStockLevel { get; set; }

    public bool IsLowStock { get; set; }

    public DateTime UpdatedAt { get; set; }
}
