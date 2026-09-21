namespace SmartRation.Api.DTOs.Ration;

public class TokenDto
{
    public int Id { get; set; }

    public string TokenNumber { get; set; } = string.Empty;

    public string Status { get; set; } = string.Empty;

    public int UserId { get; set; }

    public string UserName { get; set; } = string.Empty;

    public int RationShopId { get; set; }

    public string RationShopName { get; set; } = string.Empty;

    public int TimeSlotId { get; set; }

    public DateTime SlotDate { get; set; }

    public TimeSpan StartTime { get; set; }

    public TimeSpan EndTime { get; set; }

    public string? QRCodeValue { get; set; }

    public List<TokenItemDto> Items { get; set; } = [];

    public DateTime CreatedAt { get; set; }

    public DateTime? CollectedAt { get; set; }
}
