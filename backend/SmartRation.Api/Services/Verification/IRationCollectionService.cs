using SmartRation.Api.DTOs.Verification;

namespace SmartRation.Api.Services.Verification;

public interface IRationCollectionService
{
    Task<CollectionReceiptDto> ConfirmCollectionAsync(int tokenId, string verificationMethod);
}
