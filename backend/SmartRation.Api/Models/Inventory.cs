namespace SmartRation.Api.Models;

public enum RationType
{
    Rice = 1,
    Wheat = 2,
    Sugar = 3,
    Pulses = 4,
    EdibleOil = 5,
    Salt = 6
}

public class Inventory
{
    public int Id { get; set; }

    public int RationShopId { get; set; }

    public RationShop RationShop { get; set; } = null!;

    public RationType RationType { get; set; }

    // Concurrency token: two counters issuing from the same stock at the same
    // moment can't both succeed against a stale balance (the loser rolls back).
    [System.ComponentModel.DataAnnotations.ConcurrencyCheck]
    public decimal AvailableQuantity { get; set; }

    public decimal AllocatedQuantity { get; set; }

    public decimal MinimumStockLevel { get; set; }

    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}