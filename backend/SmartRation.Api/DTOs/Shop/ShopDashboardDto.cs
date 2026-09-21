using SmartRation.Api.DTOs.Inventory;

namespace SmartRation.Api.DTOs.Shop;

public class ShopDashboardDto
{
    public int ShopId { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public int TodayTotalTokens { get; set; }

    public int TodayCompleted { get; set; }

    public int TodayPending { get; set; }

    public int TodayCancelled { get; set; }

    public List<InventoryDto> Inventory { get; set; } = [];
}
