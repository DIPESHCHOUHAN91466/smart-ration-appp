using SmartRation.Api.DTOs.Inventory;

namespace SmartRation.Api.DTOs.Map;

public class ShopMapDetailDto
{
    public int Id { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public string ShopCode { get; set; } = string.Empty;

    public string? OperatorName { get; set; }

    public string Village { get; set; } = string.Empty;

    public string District { get; set; } = string.Empty;

    public string State { get; set; } = string.Empty;

    public double Latitude { get; set; }

    public double Longitude { get; set; }

    public List<InventoryDto> Inventory { get; set; } = [];

    public int TodayBookings { get; set; }

    public int CompletedCollections { get; set; }

    public int PendingCollections { get; set; }

    public int EligibleBeneficiaries { get; set; }

    public int VerificationIssues { get; set; }
}
