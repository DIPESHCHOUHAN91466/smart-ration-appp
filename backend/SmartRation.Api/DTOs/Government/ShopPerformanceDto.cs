namespace SmartRation.Api.DTOs.Government;

public class ShopPerformanceDto
{
    public int ShopId { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public int TotalTokens { get; set; }

    public int CompletedTokens { get; set; }

    public double EfficiencyPercent { get; set; }
}
