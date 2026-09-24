using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Qr;

namespace SmartRation.Api.Services;

public interface IQrService
{
    // Deterministic, non-guessable value containing only the token id + an
    // HMAC signature — never personal data (Phase 10 requirement).
    string ComputeQrValue(int tokenId, string tokenNumber);

    Task<string> RegenerateForTokenAsync(int tokenId);

    Task<TokenDto> VerifyAsync(string qrValue);

    // Resolves + signature-validates a QR value into its Token, with shop
    // scoping, but WITHOUT rejecting on Completed/Cancelled status — used by
    // the beneficiary verification flow, which needs to show a "blocked"
    // screen (not a bare HTTP error) for an already-used or cancelled token.
    Task<Token> ResolveTokenForVerificationAsync(string qrValue);

    // Builds the signed JSON envelope (see QrPayloadContract) for a token.
    // Token.TimeSlot must be loaded.
    string BuildSignedPayload(Token token);

    // Owner-scoped: returns the signed envelope for the caller's own token.
    Task<string> GetPayloadForTokenAsync(int tokenId);

    // Accepts either a signed JSON envelope or a bare SRQR reference (manual
    // entry / legacy QR). Validates envelope structure, project, type,
    // signature and expiry; throws an ApiException with an ErrorCode on failure.
    ParsedQr ParseScannedQr(string rawQr);
}
