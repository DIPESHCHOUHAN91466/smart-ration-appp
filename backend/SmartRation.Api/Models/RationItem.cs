namespace SmartRation.Api.Models;

// Catalog of ration commodities available for booking. Keyed by the same
// RationType enum used on Inventory, so new commodities only need a new
// enum member plus one catalog row.
public class RationItem
{
    public int Id { get; set; }

    public RationType RationType { get; set; }

    public string Name { get; set; } = string.Empty;

    public string VernacularName { get; set; } = string.Empty;

    public string Unit { get; set; } = "kg";

    public decimal StandardQuotaPerBooking { get; set; }

    public bool IsActive { get; set; } = true;
}
