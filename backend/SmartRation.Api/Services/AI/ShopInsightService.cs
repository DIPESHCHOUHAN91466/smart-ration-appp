using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.AI;

public class ShopInsightService(
    SmartRationDbContext db,
    IInventoryRiskService inventoryRisk,
    IDemandForecastService demandForecast,
    IQueuePredictionService queuePrediction) : IShopInsightService
{
    public async Task<ShopRiskInsightDto> GetShopInsightAsync(int shopId)
    {
        var shop = await db.RationShops.FirstOrDefaultAsync(s => s.Id == shopId)
            ?? throw new NotFoundException("Ration shop not found.");

        var risks = await inventoryRisk.GetRisksAsync(shopId);
        var inventoryHealth = risks.Any(r => r.CurrentStatus == "CRITICAL") ? "CRITICAL" : risks.Any(r => r.CurrentStatus == "LOW") ? "LOW" : "NORMAL";

        var demand = await demandForecast.GetForecastAsync(shopId);
        var avgGrowth = demand.Count > 0 ? demand.Average(d => d.GrowthPercent) : 0;
        var demandLevel = avgGrowth > 15 ? "HIGH" : avgGrowth > 0 ? "MODERATE" : "STABLE";

        var queue = await queuePrediction.GetPredictionsAsync(shopId);
        var wait = queue.FirstOrDefault()?.PredictedWaitMinutes ?? 0;
        var queueHealth = wait > 60 ? "HIGH" : wait > 20 ? "MODERATE" : "LOW";

        var alerts = await db.AIAlerts.CountAsync(a => a.ShopId == shopId && a.Status == AIAlertStatus.Open);
        var anomalyLevel = alerts >= 3 ? "HIGH" : alerts >= 1 ? "MEDIUM" : "LOW";

        var recommendation = inventoryHealth == "CRITICAL"
            ? $"Increase stock before predicted demand{(avgGrowth > 0 ? $" (+{avgGrowth:0.#}% trend)" : "")} — inventory is critical."
            : demandLevel == "HIGH"
                ? "Demand is trending up — consider a stock top-up ahead of the predicted peak."
                : queueHealth == "HIGH"
                    ? "Queue wait times are high — consider adding an additional counter slot."
                    : anomalyLevel != "LOW"
                        ? "Review recent anomaly alerts for this shop."
                        : "No immediate action required.";

        var overallRisk = anomalyLevel == "HIGH" || inventoryHealth == "CRITICAL"
            ? AIRiskLevel.High
            : anomalyLevel == "MEDIUM" || inventoryHealth == "LOW" || queueHealth == "HIGH"
                ? AIRiskLevel.Medium
                : AIRiskLevel.Low;

        db.AIInsights.Add(new AIInsight
        {
            EntityType = "Shop",
            EntityId = shop.Id,
            InsightType = "ShopRisk",
            RiskLevel = overallRisk,
            Score = avgGrowth,
            Explanation = $"Inventory {inventoryHealth}, demand {demandLevel}, queue {queueHealth}, anomalies {anomalyLevel}.",
            Recommendation = recommendation
        });
        await db.SaveChangesAsync();

        return new ShopRiskInsightDto
        {
            ShopId = shop.Id,
            ShopName = shop.ShopName,
            InventoryHealth = inventoryHealth,
            DemandLevel = demandLevel,
            QueueHealth = queueHealth,
            AnomalyLevel = anomalyLevel,
            Recommendation = recommendation
        };
    }
}
