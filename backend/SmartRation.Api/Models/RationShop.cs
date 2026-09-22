namespace SmartRation.Api.Models;

public class RationShop
{
    public int Id { get; set; }

    public string ShopName { get; set; } = string.Empty;

    public string ShopCode { get; set; } = string.Empty;

    public string Address { get; set; } = string.Empty;

    public string District { get; set; } = string.Empty;

    public string State { get; set; } = string.Empty;

    // Optional finer-grained administrative area, used by the map filters.
    public string? Taluka { get; set; }

    public string? Village { get; set; }

    public double Latitude { get; set; }

    public double Longitude { get; set; }

    public bool IsActive { get; set; } = true;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<User> Users { get; set; } = new List<User>();

    public ICollection<TimeSlot> TimeSlots { get; set; } = new List<TimeSlot>();

    public ICollection<Token> Tokens { get; set; } = new List<Token>();

    public ICollection<Inventory> InventoryItems { get; set; } = new List<Inventory>();

    public ICollection<Family> Families { get; set; } = new List<Family>();
}