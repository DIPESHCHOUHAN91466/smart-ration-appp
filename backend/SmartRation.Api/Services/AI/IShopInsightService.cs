using SmartRation.Api.DTOs.AI;

namespace SmartRation.Api.Services.AI;

public interface IShopInsightService
{
    Task<ShopRiskInsightDto> GetShopInsightAsync(int shopId);
}
