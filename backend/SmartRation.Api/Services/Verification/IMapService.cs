using SmartRation.Api.DTOs.Map;

namespace SmartRation.Api.Services.Verification;

public interface IMapService
{
    Task<List<ShopMapMarkerDto>> GetShopMarkersAsync(
        string? state, string? district, string? taluka, string? village, string? schemeCode, string? inventoryStatus);

    Task<ShopMapDetailDto> GetShopDetailAsync(int shopId);

    Task<MapAnalyticsDto> GetAnalyticsAsync();
}
