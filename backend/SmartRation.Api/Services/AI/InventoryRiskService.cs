using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.AI;

namespace SmartRation.Api.Services.AI;

public class InventoryRiskService(SmartRationDbContext db) : IInventoryRiskService
{
    public async Task<List<InventoryRiskDto>> GetRisksAsync(int? shopId = null)
    {
        var inventoryQuery = db.Inventory.Include(i => i.RationShop).AsQueryable();
        if (shopId.HasValue)
        {
            inventoryQuery = inventoryQuery.Where(i => i.RationShopId == shopId.Value);
        }
        var inventory = await inventoryQuery.ToListAsync();

        var fourteenDaysAgo = DateTime.UtcNow.AddDays(-14);
        var recentConsumption = await db.RationCollectionItems
            .Where(ci => ci.RationCollection.CollectedAt >= fourteenDaysAgo)
            .Select(ci => new { ci.RationCollection.RationShopId, ci.RationType, ci.Quantity })
            .ToListAsync();

        var results = new List<InventoryRiskDto>();

        foreach (var item in inventory)
        {
            var consumed = recentConsumption
                .Where(c => c.RationShopId == item.RationShopId && c.RationType == item.RationType)
                .Sum(c => c.Quantity);
            var avgDaily = consumed / 14m;

            var status = item.AvailableQuantity <= item.MinimumStockLevel * 0.5m
                ? "CRITICAL"
                : item.AvailableQuantity <= item.MinimumStockLevel
                    ? "LOW"
                    : "NORMAL";

            double? daysUntilReorder = avgDaily > 0
                ? (double)((item.AvailableQuantity - item.MinimumStockLevel) / avgDaily)
                : null;

            var explanation = avgDaily > 0
                ? $"Consuming ~{avgDaily:0.#} kg/day over the last 14 days; {item.AvailableQuantity} kg on hand."
                : $"No recent consumption recorded; {item.AvailableQuantity} kg on hand.";

            results.Add(new InventoryRiskDto
            {
                ShopId = item.RationShopId,
                ShopName = item.RationShop.ShopName,
                RationType = item.RationType.ToString(),
                CurrentStatus = status,
                AvailableQuantity = item.AvailableQuantity,
                AverageDailyConsumption = Math.Round(avgDaily, 2),
                PredictedDaysUntilReorder = daysUntilReorder.HasValue ? Math.Round(daysUntilReorder.Value, 1) : null,
                Explanation = explanation
            });
        }

        return results;
    }
}
