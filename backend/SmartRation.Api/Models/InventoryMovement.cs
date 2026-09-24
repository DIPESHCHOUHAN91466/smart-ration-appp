namespace SmartRation.Api.Models;

public enum InventoryMovementType
{
    Received = 1,     // stock delivered to the shop (e.g. against a challan)
    Distributed = 2,  // issued to a beneficiary through a collection
    Damaged = 3,      // spoiled / damaged / written off
    Adjustment = 4    // manual correction; Quantity may be negative
}

// Append-only stock ledger. Inventory.AvailableQuantity stays the fast
// "current balance"; this table records WHY it changed, so received,
// distributed and damaged totals, daily consumption and stock-vs-distribution
// variance can be computed (by the Python AI service and reports) instead of
// only knowing today's number. Rows are never updated or deleted.
public class InventoryMovement
{
    public long Id { get; set; }

    public int RationShopId { get; set; }

    public RationShop RationShop { get; set; } = null!;

    public RationType RationType { get; set; }

    public InventoryMovementType MovementType { get; set; }

    // Positive for Received/Distributed/Damaged; signed for Adjustment.
    public decimal Quantity { get; set; }

    // Balance immediately after this movement — makes the ledger auditable
    // on its own (a gap between consecutive rows reveals an off-ledger edit).
    public decimal BalanceAfter { get; set; }

    // Collection code, delivery challan number, etc. Never personal data.
    public string? Reference { get; set; }

    public string? Note { get; set; }

    public int? RecordedByUserId { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
