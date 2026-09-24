using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Inventory;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public class InventoryService(
    SmartRationDbContext db,
    ICurrentUserService currentUser,
    INotificationService notificationService) : IInventoryService
{
    public async Task<IReadOnlyList<InventoryDto>> GetInventoryAsync(int? shopId)
    {
        var effectiveShopId = ResolveShopIdForRead(shopId);

        var query = db.Inventory.AsQueryable();
        if (effectiveShopId.HasValue)
        {
            query = query.Where(i => i.RationShopId == effectiveShopId.Value);
        }

        var items = await query.OrderBy(i => i.RationShopId).ThenBy(i => i.RationType).ToListAsync();
        return items.Select(i => i.ToDto()).ToList();
    }

    public async Task<InventoryDto> CreateInventoryAsync(CreateInventoryRequestDto request)
    {
        var shop = await db.RationShops.FirstOrDefaultAsync(s => s.Id == request.RationShopId)
            ?? throw new NotFoundException("Ration shop not found.");

        EnsureCanManage(shop.Id);

        if (!Enum.TryParse<RationType>(request.RationType, ignoreCase: true, out var rationType))
        {
            throw new BadRequestException($"Unknown ration item '{request.RationType}'.");
        }

        var exists = await db.Inventory.AnyAsync(i => i.RationShopId == shop.Id && i.RationType == rationType);
        if (exists)
        {
            throw new ConflictException($"Inventory for {rationType} already exists at this shop. Use the update endpoint instead.");
        }

        var inventory = new Inventory
        {
            RationShopId = shop.Id,
            RationType = rationType,
            AvailableQuantity = request.AvailableQuantity,
            AllocatedQuantity = 0,
            MinimumStockLevel = request.MinimumStockLevel,
            UpdatedAt = DateTime.UtcNow
        };

        db.Inventory.Add(inventory);
        await db.SaveChangesAsync();

        if (inventory.AvailableQuantity > 0)
        {
            InventoryLedger.Record(db, inventory, InventoryMovementType.Received, inventory.AvailableQuantity, currentUser.UserId, note: "Opening stock");
            await db.SaveChangesAsync();
        }

        return inventory.ToDto();
    }

    public async Task<InventoryDto> UpdateInventoryAsync(int id, UpdateInventoryRequestDto request)
    {
        var inventory = await db.Inventory.FirstOrDefaultAsync(i => i.Id == id)
            ?? throw new NotFoundException("Inventory record not found.");

        EnsureCanManage(inventory.RationShopId);

        var delta = request.AvailableQuantity - inventory.AvailableQuantity;

        inventory.AvailableQuantity = request.AvailableQuantity;
        inventory.MinimumStockLevel = request.MinimumStockLevel;
        inventory.UpdatedAt = DateTime.UtcNow;

        // A direct balance edit is a manual correction — keep it visible in the ledger.
        if (delta != 0)
        {
            InventoryLedger.Record(db, inventory, InventoryMovementType.Adjustment, delta, currentUser.UserId, note: "Manual stock correction");
        }

        await db.SaveChangesAsync();

        if (inventory.AvailableQuantity <= inventory.MinimumStockLevel)
        {
            var shopOwners = await db.Users
                .Where(u => u.RationShopId == inventory.RationShopId && u.Role == UserRole.ShopOwner)
                .ToListAsync();

            foreach (var owner in shopOwners)
            {
                await notificationService.CreateAsync(
                    owner.Id,
                    NotificationType.LowInventory,
                    "Low stock alert",
                    $"{inventory.RationType} is running low ({inventory.AvailableQuantity} remaining, threshold {inventory.MinimumStockLevel}).");
            }
        }

        return inventory.ToDto();
    }

    public async Task<InventoryDto> ReceiveStockAsync(int id, StockMovementRequestDto request)
    {
        var inventory = await LoadManagedAsync(id);

        inventory.AvailableQuantity += request.Quantity;
        inventory.UpdatedAt = DateTime.UtcNow;
        InventoryLedger.Record(db, inventory, InventoryMovementType.Received, request.Quantity, currentUser.UserId, request.Reference, request.Note);

        await db.SaveChangesAsync();
        return inventory.ToDto();
    }

    public async Task<InventoryDto> RecordDamageAsync(int id, StockMovementRequestDto request)
    {
        var inventory = await LoadManagedAsync(id);

        if (request.Quantity > inventory.AvailableQuantity)
        {
            throw new BadRequestException($"Cannot write off {request.Quantity} — only {inventory.AvailableQuantity} in stock.") { ErrorCode = "INSUFFICIENT_STOCK" };
        }

        inventory.AvailableQuantity -= request.Quantity;
        inventory.UpdatedAt = DateTime.UtcNow;
        InventoryLedger.Record(db, inventory, InventoryMovementType.Damaged, request.Quantity, currentUser.UserId, request.Reference, request.Note);

        await db.SaveChangesAsync();
        return inventory.ToDto();
    }

    private async Task<Inventory> LoadManagedAsync(int id)
    {
        var inventory = await db.Inventory.FirstOrDefaultAsync(i => i.Id == id)
            ?? throw new NotFoundException("Inventory record not found.");
        EnsureCanManage(inventory.RationShopId);
        return inventory;
    }

    private int? ResolveShopIdForRead(int? requestedShopId)
    {
        return currentUser.Role switch
        {
            UserRole.ShopOwner => currentUser.RationShopId,
            UserRole.GovernmentOfficial or UserRole.Admin => requestedShopId,
            _ => throw new ForbiddenException("You do not have permission to view inventory.")
        };
    }

    private void EnsureCanManage(int shopId)
    {
        var allowed = currentUser.Role switch
        {
            UserRole.ShopOwner => currentUser.RationShopId == shopId,
            UserRole.GovernmentOfficial or UserRole.Admin => true,
            _ => false
        };

        if (!allowed)
        {
            throw new ForbiddenException("You do not have permission to manage inventory for this shop.");
        }
    }
}
