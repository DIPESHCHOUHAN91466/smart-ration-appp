namespace SmartRation.Api.Models;

public enum AIRiskLevel
{
    Low = 1,
    Medium = 2,
    High = 3
}

// Decision-support output only — AI never denies benefits, declares fraud,
// or cancels entitlement on its own. A human always acts on the
// recommendation. Every insight carries its own explanation, computed from
// real (synthetic-seeded) data, never a hard-coded label.
public class AIInsight
{
    public int Id { get; set; }

    public string EntityType { get; set; } = string.Empty; // Beneficiary | Shop | System

    public int? EntityId { get; set; }

    public string InsightType { get; set; } = string.Empty; // DemandForecast | InventoryRisk | QueuePrediction | AnomalyRisk | ShopRisk

    public AIRiskLevel RiskLevel { get; set; }

    public double Score { get; set; }

    public string Explanation { get; set; } = string.Empty;

    public string Recommendation { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
