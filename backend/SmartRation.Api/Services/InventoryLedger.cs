using SmartRation.Api.Data;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

// Appends InventoryMovement rows next to every stock change. Does NOT call
// SaveChanges: the movement is saved in the same unit of work (and, for
// collections, the same transaction) as the Inventory balance change, so the
// ledger and the balance can never disagree.
public static class InventoryLedger
{
    public static InventoryMovement Record(
        SmartRationDbContext db,
        Inventory inventory,
        InventoryMovementType type,
        decimal quantity,
        int? userId,
        string? reference = null,
        string? note = null)
    {
        var movement = new InventoryMovement
        {
            RationShopId = inventory.RationShopId,
            RationType = inventory.RationType,
            MovementType = type,
            Quantity = quantity,
            BalanceAfter = inventory.AvailableQuantity,
            Reference = reference,
            Note = note,
            RecordedByUserId = userId,
            CreatedAt = DateTime.UtcNow
        };
        db.InventoryMovements.Add(movement);
        return movement;
    }
}
