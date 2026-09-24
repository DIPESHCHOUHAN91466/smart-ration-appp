namespace SmartRation.Api.DTOs.AI;

public class DemandForecastDto
{
    public string RationType { get; set; } = string.Empty;

    public decimal Last30DaysKg { get; set; }

    public decimal Previous30DaysKg { get; set; }

    public double GrowthPercent { get; set; }

    public decimal PredictedNext30DaysKg { get; set; }
}

public class InventoryRiskDto
{
    public int ShopId { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public string RationType { get; set; } = string.Empty;

    public string CurrentStatus { get; set; } = string.Empty; // NORMAL | LOW | CRITICAL

    public decimal AvailableQuantity { get; set; }

    public decimal AverageDailyConsumption { get; set; }

    public double? PredictedDaysUntilReorder { get; set; }

    public string Explanation { get; set; } = string.Empty;
}

public class QueuePredictionDto
{
    public int ShopId { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public int PendingInQueue { get; set; }

    public int PredictedWaitMinutes { get; set; }

    public string Explanation { get; set; } = string.Empty;
}

public class AnomalyAlertDto
{
    public int Id { get; set; }

    public int? ShopId { get; set; }

    public int? BeneficiaryId { get; set; }

    public string AlertType { get; set; } = string.Empty;

    public string Severity { get; set; } = string.Empty;

    public string Description { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public string CreatedAt { get; set; } = string.Empty;
}

public class ShopRiskInsightDto
{
    public int ShopId { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public string InventoryHealth { get; set; } = string.Empty;

    public string DemandLevel { get; set; } = string.Empty;

    public string QueueHealth { get; set; } = string.Empty;

    public string AnomalyLevel { get; set; } = string.Empty;

    public string Recommendation { get; set; } = string.Empty;
}

public class BeneficiaryRiskInsightDto
{
    public string RiskLevel { get; set; } = string.Empty; // Low | Medium | High

    public List<string> Reasons { get; set; } = [];

    public string Explanation { get; set; } = string.Empty;
}

public class AIIntelligenceCenterDto
{
    public List<DemandForecastDto> DemandForecast { get; set; } = [];

    public List<InventoryRiskDto> InventoryRisks { get; set; } = [];

    public List<QueuePredictionDto> QueuePredictions { get; set; } = [];

    public List<AnomalyAlertDto> RecentAnomalies { get; set; } = [];

    public int ShopsRequiringAttention { get; set; }

    public double AverageQueueWaitMinutes { get; set; }

    public int AnomaliesRequiringReview { get; set; }

    public bool IsSyntheticData { get; set; } = true;
}
