namespace SmartRation.Api.Models;

public enum TokenStatus
{
    Pending = 1,
    Confirmed = 2,
    Completed = 3,
    Cancelled = 4,
    NoShow = 5
}

public class Token
{
    public int Id { get; set; }

    public string TokenNumber { get; set; } = string.Empty;

    public int UserId { get; set; }

    public User User { get; set; } = null!;

    public int RationShopId { get; set; }

    public RationShop RationShop { get; set; } = null!;

    public int TimeSlotId { get; set; }

    public TimeSlot TimeSlot { get; set; } = null!;

    public TokenStatus Status { get; set; } = TokenStatus.Pending;

    public string? QRCodeValue { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTime? CollectedAt { get; set; }

    public ICollection<TokenItem> Items { get; set; } = new List<TokenItem>();
}