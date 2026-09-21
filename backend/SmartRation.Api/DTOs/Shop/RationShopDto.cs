namespace SmartRation.Api.DTOs.Shop;

public class RationShopDto
{
    public int Id { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public string ShopCode { get; set; } = string.Empty;

    public string Address { get; set; } = string.Empty;

    public string District { get; set; } = string.Empty;

    public string State { get; set; } = string.Empty;

    public bool IsActive { get; set; }
}
