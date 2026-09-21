namespace SmartRation.Api.DTOs.Users;

public class UserSummaryDto
{
    public int Id { get; set; }

    public string FullName { get; set; } = string.Empty;

    public string Email { get; set; } = string.Empty;

    public string MobileNumber { get; set; } = string.Empty;

    public string Role { get; set; } = string.Empty;

    public int? RationShopId { get; set; }
}
