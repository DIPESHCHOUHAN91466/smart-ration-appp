using SmartRation.Api.DTOs.Inventory;
using SmartRation.Api.Models;

namespace SmartRation.Api.Mapping;

public static class InventoryMappingExtensions
{
    public static InventoryDto ToDto(this Inventory inventory) => new()
    {
        Id = inventory.Id,
        RationShopId = inventory.RationShopId,
        RationType = inventory.RationType.ToString(),
        AvailableQuantity = inventory.AvailableQuantity,
        AllocatedQuantity = inventory.AllocatedQuantity,
        MinimumStockLevel = inventory.MinimumStockLevel,
        IsLowStock = inventory.AvailableQuantity <= inventory.MinimumStockLevel,
        UpdatedAt = inventory.UpdatedAt
    };
}
