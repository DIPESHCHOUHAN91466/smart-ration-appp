using SmartRation.Api.DTOs.Inventory;

namespace SmartRation.Api.Services;

public interface IInventoryService
{
    Task<IReadOnlyList<InventoryDto>> GetInventoryAsync(int? shopId);

    Task<InventoryDto> CreateInventoryAsync(CreateInventoryRequestDto request);

    Task<InventoryDto> UpdateInventoryAsync(int id, UpdateInventoryRequestDto request);

    // Stock delivered to the shop (adds to the balance, recorded as Received).
    Task<InventoryDto> ReceiveStockAsync(int id, StockMovementRequestDto request);

    // Damaged / spoiled stock written off (recorded as Damaged).
    Task<InventoryDto> RecordDamageAsync(int id, StockMovementRequestDto request);
}
