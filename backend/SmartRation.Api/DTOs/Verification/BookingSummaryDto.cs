namespace SmartRation.Api.DTOs.Verification;

public class BookingSummaryDto
{
    public int TokenId { get; set; }

    public string TokenNumber { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public string CollectionDate { get; set; } = string.Empty;

    public string BookingTime { get; set; } = string.Empty;

    public int ShopId { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public string ShopCode { get; set; } = string.Empty;

    public bool CollectionCompleted { get; set; }
}

public class CollectedItemDto
{
    public string RationType { get; set; } = string.Empty;

    public decimal Quantity { get; set; }
}

public class CollectionHistoryItemDto
{
    public string CollectionCode { get; set; } = string.Empty;

    public string CollectedAt { get; set; } = string.Empty;

    public string ShopName { get; set; } = string.Empty;

    public List<CollectedItemDto> Items { get; set; } = [];
}
