using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

// Abstraction over "what is this beneficiary's Aadhaar verification status."
// SyntheticAadhaarVerificationService is the only implementation today; a
// future AuthorizedAadhaarVerificationService would call a real eKYC
// provider here instead — nothing above this interface would change.
public interface IAadhaarVerificationService
{
    Task<AadhaarVerification> GetOrCreateAsync(int beneficiaryId);
}
