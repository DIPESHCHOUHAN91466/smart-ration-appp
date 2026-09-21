using SmartRation.Api.DTOs.Inventory;

namespace SmartRation.Api.Services;

public interface IInventoryService
{
    Task<IReadOnlyList<InventoryDto>> GetInventoryAsync(int? shopId);

    Task<InventoryDto> CreateInventoryAsync(CreateInventoryRequestDto request);

    Task<InventoryDto> UpdateInventoryAsync(int id, UpdateInventoryRequestDto request);
}
