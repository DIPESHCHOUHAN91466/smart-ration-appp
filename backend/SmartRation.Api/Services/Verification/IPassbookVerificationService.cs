using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

public interface IPassbookVerificationService
{
    Task<PassbookVerification> GetOrCreateAsync(int beneficiaryId);
}
