using SmartRation.Api.DTOs.Ration;

namespace SmartRation.Api.Services;

public interface IQrService
{
    // Deterministic, non-guessable value containing only the token id + an
    // HMAC signature — never personal data (Phase 10 requirement).
    string ComputeQrValue(int tokenId, string tokenNumber);

    Task<string> RegenerateForTokenAsync(int tokenId);

    Task<TokenDto> VerifyAsync(string qrValue);
}
