using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.AI;

public class AIIntelligenceService(
    IDemandForecastService demandForecast,
    IInventoryRiskService inventoryRisk,
    IQueuePredictionService queuePrediction,
    IAnomalyDetectionService anomalyDetection) : IAIIntelligenceService
{
    public async Task<AIIntelligenceCenterDto> GetIntelligenceCenterAsync()
    {
        await anomalyDetection.ScanAndDetectAsync();

        var demand = await demandForecast.GetForecastAsync();
        var inventory = await inventoryRisk.GetRisksAsync();
        var queue = await queuePrediction.GetPredictionsAsync();
        var alerts = await anomalyDetection.GetRecentAlertsAsync();

        return new AIIntelligenceCenterDto
        {
            DemandForecast = demand,
            InventoryRisks = inventory,
            QueuePredictions = queue,
            RecentAnomalies = alerts.Select(a => new AnomalyAlertDto
            {
                Id = a.Id,
                ShopId = a.ShopId,
                BeneficiaryId = a.BeneficiaryId,
                AlertType = a.AlertType,
                Severity = a.Severity.ToString(),
                Description = a.Description,
                Status = a.Status.ToString(),
                CreatedAt = a.CreatedAt.ToString("yyyy-MM-dd HH:mm")
            }).ToList(),
            ShopsRequiringAttention = inventory.Select(i => i.ShopId).Distinct().Count(i => inventory.Any(r => r.ShopId == i && r.CurrentStatus != "NORMAL")),
            AverageQueueWaitMinutes = queue.Count > 0 ? Math.Round(queue.Average(q => q.PredictedWaitMinutes), 1) : 0,
            AnomaliesRequiringReview = alerts.Count(a => a.Status == AIAlertStatus.Open),
            IsSyntheticData = true
        };
    }
}
