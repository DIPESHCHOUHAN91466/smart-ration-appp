using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public interface IJwtService
{
    (string Token, DateTime ExpiresAt) GenerateAccessToken(User user);

    (string RawToken, string TokenHash, DateTime ExpiresAt) GenerateRefreshToken();

    string HashToken(string rawToken);
}
