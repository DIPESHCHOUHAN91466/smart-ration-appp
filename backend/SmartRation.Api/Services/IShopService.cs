using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.DTOs.Shop;

namespace SmartRation.Api.Services;

public interface IShopService
{
    Task<ShopDashboardDto> GetDashboardAsync();

    Task<TokenDto> CompleteCollectionAsync(int tokenId, string? idempotencyKey = null);
}
