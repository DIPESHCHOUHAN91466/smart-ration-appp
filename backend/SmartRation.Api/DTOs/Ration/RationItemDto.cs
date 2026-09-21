namespace SmartRation.Api.DTOs.Ration;

public class RationItemDto
{
    public int Id { get; set; }

    public string RationType { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string VernacularName { get; set; } = string.Empty;

    public string Unit { get; set; } = string.Empty;

    public decimal StandardQuotaPerBooking { get; set; }
}
