namespace SmartRation.Api.DTOs.Admin;

public class FamilyMemberRowDto
{
    public int Id { get; set; }
    public string FamilyCode { get; set; } = string.Empty;
    public string FullName { get; set; } = string.Empty;
    public int Age { get; set; }
    public string Relationship { get; set; } = string.Empty;
    public string Eligibility { get; set; } = string.Empty;
}

public class TokenRowDto
{
    public int Id { get; set; }
    public string TokenNumber { get; set; } = string.Empty;
    public string BeneficiaryCode { get; set; } = string.Empty;
    public string ShopName { get; set; } = string.Empty;
    public string SlotDate { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string? QrCodeValue { get; set; }
}

public class CollectionRowDto
{
    public int Id { get; set; }
    public string CollectionCode { get; set; } = string.Empty;
    public string BeneficiaryCode { get; set; } = string.Empty;
    public string ShopName { get; set; } = string.Empty;
    public string CollectedAt { get; set; } = string.Empty;
    public decimal TotalQuantityKg { get; set; }
}

public class InventoryRowDto
{
    public int Id { get; set; }
    public string ShopName { get; set; } = string.Empty;
    public string RationType { get; set; } = string.Empty;
    public decimal Available { get; set; }
    public decimal Allocated { get; set; }
    public decimal MinimumStockLevel { get; set; }
}

public class AIInsightRowDto
{
    public int Id { get; set; }
    public string EntityType { get; set; } = string.Empty;
    public int? EntityId { get; set; }
    public string InsightType { get; set; } = string.Empty;
    public string RiskLevel { get; set; } = string.Empty;
    public double Score { get; set; }
    public string Explanation { get; set; } = string.Empty;
    public string CreatedAt { get; set; } = string.Empty;
}
