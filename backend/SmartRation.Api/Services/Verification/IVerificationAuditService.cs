using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

public interface IVerificationAuditService
{
    Task LogAsync(
        VerificationAction action,
        string status,
        string verificationMethod,
        string? verificationReference = null,
        string? tokenNumber = null,
        int? beneficiaryId = null,
        int? shopId = null,
        string? reason = null);
}
