namespace SmartRation.Api.DTOs.Verification;

public class VerificationAuditLogDto
{
    public long Id { get; set; }

    public string? VerificationReference { get; set; }

    public string? TokenNumber { get; set; }

    public int? BeneficiaryId { get; set; }

    public int? ShopId { get; set; }

    public string Action { get; set; } = string.Empty;

    public string VerificationMethod { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public string? Reason { get; set; }

    public int? OperatorId { get; set; }

    public string Timestamp { get; set; } = string.Empty;
}
