namespace SmartRation.Api.DTOs.Ration;

public class RationItemDto
{
    public int Id { get; set; }

    public string RationType { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string VernacularName { get; set; } = string.Empty;

    public string Unit { get; set; } = string.Empty;

    public decimal StandardQuotaPerBooking { get; set; }

    // Populated only when the caller passes ?shopId= — the shop's current
    // available stock for this item, read-only (never exposes minimum
    // stock level or other shop-management fields).
    public decimal? AvailableQuantity { get; set; }

    // Populated only for a RuralUser caller — how much of this item their
    // family can still collect this month under their active scheme, i.e.
    // entitlement-derived, never a hardcoded universal quota.
    public decimal? EligibleQuantity { get; set; }
}
