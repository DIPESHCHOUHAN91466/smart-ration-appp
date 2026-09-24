namespace SmartRation.Api.Models;

public class AuditLog
{
    public long Id { get; set; }

    public int? UserId { get; set; }

    public string Action { get; set; } = string.Empty;

    public string EntityName { get; set; } = string.Empty;

    public string? EntityId { get; set; }

    public string? IpAddress { get; set; }

    public string? Details { get; set; }

    // Actor's role at the time (RuralUser / ShopOwner / ...), from the JWT.
    public string? Role { get; set; }

    // SUCCESS / FAILED / BLOCKED.
    public string? Result { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}