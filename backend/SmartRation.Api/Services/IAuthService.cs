using SmartRation.Api.DTOs.Auth;

namespace SmartRation.Api.Services;

public interface IAuthService
{
    Task<AuthResponseDto> RegisterAsync(RegisterRequestDto request);

    Task<AuthResponseDto> LoginAsync(LoginRequestDto request);

    Task<AuthResponseDto> RefreshAsync(string rawRefreshToken);

    Task LogoutAsync(string rawRefreshToken);
}
