namespace SmartRation.Api.DTOs.Verification;

public class EntitlementItemDto
{
    public string RationType { get; set; } = string.Empty;

    public decimal MonthlyEntitlement { get; set; }

    public decimal AlreadyCollected { get; set; }

    public decimal Remaining { get; set; }

    public decimal TodayAllocation { get; set; }
}

public class EntitlementSummaryDto
{
    public string SchemeCode { get; set; } = string.Empty;

    public string SchemeName { get; set; } = string.Empty;

    public int FamilySize { get; set; }

    public int EligibleMemberCount { get; set; }

    public List<EntitlementItemDto> Items { get; set; } = [];
}
