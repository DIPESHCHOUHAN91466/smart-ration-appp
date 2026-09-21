using SmartRation.Api.DTOs.Users;

namespace SmartRation.Api.DTOs.Auth;

public class AuthResponseDto
{
    public string AccessToken { get; set; } = string.Empty;

    public string RefreshToken { get; set; } = string.Empty;

    public DateTime AccessTokenExpiresAt { get; set; }

    public UserSummaryDto User { get; set; } = null!;
}
