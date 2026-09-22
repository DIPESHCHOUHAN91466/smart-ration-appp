namespace SmartRation.Api.Models;

public enum UserRole
{
    RuralUser = 1,
    ShopOwner = 2,
    GovernmentOfficial = 3,
    Admin = 4
}

public class User
{
    public int Id { get; set; }

    public string FullName { get; set; } = string.Empty;

    public string Email { get; set; } = string.Empty;

    public string MobileNumber { get; set; } = string.Empty;

    // In production, never store a plain-text password.
    public string PasswordHash { get; set; } = string.Empty;

    public UserRole Role { get; set; }

    public bool IsActive { get; set; } = true;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Optional shop relationship for Shop Owners
    public int? RationShopId { get; set; }

    public RationShop? RationShop { get; set; }

    public ICollection<Token> Tokens { get; set; } = new List<Token>();

    public ICollection<RefreshToken> RefreshTokens { get; set; } = new List<RefreshToken>();

    public ICollection<Notification> Notifications { get; set; } = new List<Notification>();

    public Beneficiary? Beneficiary { get; set; }
}