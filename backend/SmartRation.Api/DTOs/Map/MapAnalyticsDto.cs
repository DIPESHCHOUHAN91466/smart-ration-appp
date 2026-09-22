namespace SmartRation.Api.DTOs.Map;

public class HeatmapPointDto
{
    public double Lat { get; set; }

    public double Lng { get; set; }

    public double Intensity { get; set; }
}

public class MapAnalyticsDto
{
    public int TotalShops { get; set; }

    public int ActiveShops { get; set; }

    public int LowInventoryShops { get; set; }

    public int CriticalInventoryShops { get; set; }

    public int TotalBeneficiaries { get; set; }

    public int EligibleBeneficiaries { get; set; }

    public int TodayCollections { get; set; }

    public int PendingCollections { get; set; }

    // Shop-level weighted points only — never individual beneficiary
    // locations (none exist; this system has no real residential data).
    public List<HeatmapPointDto> BeneficiaryDensityHeatmap { get; set; } = [];

    public List<HeatmapPointDto> DemandHeatmap { get; set; } = [];

    public List<HeatmapPointDto> CollectionActivityHeatmap { get; set; } = [];

    public List<HeatmapPointDto> InventoryShortageHeatmap { get; set; } = [];

    public bool IsSyntheticData { get; set; } = true;
}
