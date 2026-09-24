using SmartRation.Api.DTOs.Verification;

namespace SmartRation.Api.Services.Verification;

public interface IRationCollectionService
{
    // idempotencyKey: optional client key; a retry with the same key returns the original receipt.
    Task<CollectionReceiptDto> ConfirmCollectionAsync(int tokenId, string verificationMethod, string? idempotencyKey = null);
}
