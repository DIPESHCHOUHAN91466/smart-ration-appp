namespace SmartRation.Api.DTOs.Government;

public class GovernmentDashboardDto
{
    public int TotalBeneficiaries { get; set; }

    public int TotalShops { get; set; }

    public int TodayBookings { get; set; }

    public int TodayCollections { get; set; }

    public int PendingCollections { get; set; }

    public decimal RationDistributedTodayKg { get; set; }

    public int LowStockAlerts { get; set; }
}
