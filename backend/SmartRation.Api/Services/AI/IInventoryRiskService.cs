using SmartRation.Api.DTOs.AI;

namespace SmartRation.Api.Services.AI;

public interface IInventoryRiskService
{
    Task<List<InventoryRiskDto>> GetRisksAsync(int? shopId = null);
}
