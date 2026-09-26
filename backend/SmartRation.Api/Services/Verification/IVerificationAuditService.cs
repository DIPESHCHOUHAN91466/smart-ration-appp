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

    // Newest first, optionally filtered; take is clamped to 1-500.
    Task<List<DTOs.Verification.VerificationAuditLogDto>> QueryAsync(int? shopId, int? beneficiaryId, string? status, int take);
}
