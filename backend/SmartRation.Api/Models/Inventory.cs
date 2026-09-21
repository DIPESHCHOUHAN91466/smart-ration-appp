namespace SmartRation.Api.Models;

public enum RationType
{
    Rice = 1,
    Wheat = 2,
    Sugar = 3
}

public class Inventory
{
    public int Id { get; set; }

    public int RationShopId { get; set; }

    public RationShop RationShop { get; set; } = null!;

    public RationType RationType { get; set; }

    public decimal AvailableQuantity { get; set; }

    public decimal AllocatedQuantity { get; set; }

    public decimal MinimumStockLevel { get; set; }

    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}