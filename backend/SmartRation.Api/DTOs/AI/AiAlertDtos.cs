using System.ComponentModel.DataAnnotations;
using System.Text.Json;
using SmartRation.Api.Models;

namespace SmartRation.Api.DTOs.AI;

public class AiAlertDto
{
    public int Id { get; set; }
    public string Source { get; set; } = string.Empty;
    public string AlertType { get; set; } = string.Empty;
    public string Severity { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public int? ShopId { get; set; }
    public string? ShopName { get; set; }
    public int? BeneficiaryId { get; set; }
    public string? RationType { get; set; }
    public string? Title { get; set; }
    public string Description { get; set; } = string.Empty;
    public double? Score { get; set; }
    public string? RecommendedAction { get; set; }
    public JsonElement? Metadata { get; set; }
    public DateTime DetectedAt { get; set; }
    public DateTime? LastSeenAt { get; set; }
    public DateTime? ResolvedAt { get; set; }
    public string? ResolutionNote { get; set; }

    // Every alert is a prompt for human review, never proof of wrongdoing.
    public string Notice => "Decision support only — not proof of fraud. Review before acting.";

    public static AiAlertDto From(AIAlert a, string? shopName) => new()
    {
        Id = a.Id,
        Source = a.Source,
        AlertType = a.AlertType,
        Severity = a.Severity.ToString().ToUpperInvariant(),
        Status = a.Status.ToString(),
        ShopId = a.ShopId,
        ShopName = shopName,
        BeneficiaryId = a.BeneficiaryId,
        RationType = a.RationType?.ToString(),
        Title = a.Title ?? a.AlertType,
        Description = a.Description,
        Score = a.Score,
        RecommendedAction = a.RecommendedAction,
        Metadata = ParseMetadata(a.MetadataJson),
        DetectedAt = a.DetectedAt ?? a.CreatedAt,
        LastSeenAt = a.LastSeenAt,
        ResolvedAt = a.ResolvedAt,
        ResolutionNote = a.ResolutionNote
    };

    private static JsonElement? ParseMetadata(string? json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            return null;
        }
        try
        {
            using var doc = JsonDocument.Parse(json);
            return doc.RootElement.Clone();
        }
        catch (JsonException)
        {
            return null;
        }
    }
}

public class AiAlertSyncResultDto
{
    public bool Available { get; set; }
    public bool Skipped { get; set; }
    public int Created { get; set; }
    public int Updated { get; set; }
    public int Rejected { get; set; }
    public DateTime? LastAnalysisAt { get; set; }
    public string? ErrorCode { get; set; }
    public string? Message { get; set; }
}

public class ResolveAiAlertRequestDto
{
    // UnderReview, Resolved or Dismissed.
    [Required]
    [RegularExpression("^(UnderReview|Resolved|Dismissed)$", ErrorMessage = "Status must be UnderReview, Resolved or Dismissed.")]
    public string Status { get; set; } = string.Empty;

    [MaxLength(500)]
    public string? Note { get; set; }
}
