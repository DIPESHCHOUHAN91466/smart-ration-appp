namespace SmartRation.Api.Models;

public enum AIAlertSeverity
{
    Info = 0,
    Low = 1,
    Medium = 2,
    High = 3,
    Critical = 4
}

public enum AIAlertStatus
{
    Open = 1,
    UnderReview = 2,
    Resolved = 3,
    Dismissed = 4
}

// Anomaly/risk alerts a human must review and act on — this table never
// drives an automatic denial or suspension by itself. An alert is NOT proof
// of fraud: it always carries its reason, score, source and supporting data.
public class AIAlert
{
    public int Id { get; set; }

    public int? ShopId { get; set; }

    public int? BeneficiaryId { get; set; }

    // Built-in rules: RepeatedQrScan | DuplicateCollectionAttempt | RepeatedFailedVerification | UnusualShopActivity
    // Python AI:      DEMAND_SPIKE | LOW_STOCK | FORECAST_RISK | UNUSUAL_CONSUMPTION | INVENTORY_ANOMALY
    public string AlertType { get; set; } = string.Empty;

    public AIAlertSeverity Severity { get; set; }

    public string Description { get; set; } = string.Empty;

    public AIAlertStatus Status { get; set; } = AIAlertStatus.Open;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime? ResolvedAt { get; set; }

    // ---- Added for persisted Python AI alerts (all nullable / defaulted, so
    // existing rule-based alerts keep working unchanged) ----

    // "RULES" (built-in C# anomaly detection) or "PYTHON_AI".
    public string Source { get; set; } = "RULES";

    public string? Title { get; set; }

    // Commodity the alert is about, when item-specific.
    public RationType? RationType { get; set; }

    // 0–100 strength of the signal, when the detector provides one.
    public double? Score { get; set; }

    public string? RecommendedAction { get; set; }

    // Stable identity of "the same finding" (e.g. LOW_STOCK:3:Rice). While an
    // alert with this key is open, re-detection updates it instead of adding a row.
    public string? DedupKey { get; set; }

    // Supporting figures behind the alert (JSON), for the reviewer.
    public string? MetadataJson { get; set; }

    public DateTime? DetectedAt { get; set; }

    public DateTime? LastSeenAt { get; set; }

    public int? ResolvedByUserId { get; set; }

    public string? ResolutionNote { get; set; }
}
