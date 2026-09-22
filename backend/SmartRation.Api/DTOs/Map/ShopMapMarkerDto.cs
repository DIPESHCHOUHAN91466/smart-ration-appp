namespace SmartRation.Api.DTOs.Map;

public class ShopMapMarkerDto
{
    public int Id { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public string ShopCode { get; set; } = string.Empty;

    public double Latitude { get; set; }

    public double Longitude { get; set; }

    public string State { get; set; } = string.Empty;

    public string District { get; set; } = string.Empty;

    public string? Taluka { get; set; }

    public string? Village { get; set; }

    // Normal | Low | Critical
    public string InventoryStatus { get; set; } = string.Empty;

    public int TodayBookings { get; set; }

    public int CompletedCollections { get; set; }

    public int PendingCollections { get; set; }

    public int EligibleBeneficiaries { get; set; }

    public int VerificationIssues { get; set; }

    public string DataSource { get; set; } = "SYNTHETIC_DEMO";
}
