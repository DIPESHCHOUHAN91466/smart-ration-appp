namespace SmartRation.Api.DTOs.Government;

public class StatisticsDto
{
    public DateTime FromDate { get; set; }

    public DateTime ToDate { get; set; }

    public int TokensGenerated { get; set; }

    public int CollectionsCompleted { get; set; }

    public int CollectionsCancelled { get; set; }

    public double CollectionEfficiencyPercent { get; set; }

    public List<ShopPerformanceDto> ShopPerformance { get; set; } = [];
}
