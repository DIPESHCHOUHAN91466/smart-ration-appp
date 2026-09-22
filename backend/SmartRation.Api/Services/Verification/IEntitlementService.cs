using SmartRation.Api.DTOs.Verification;

namespace SmartRation.Api.Services.Verification;

public interface IEntitlementService
{
    // Recalculates monthly entitlement, this-month's already-collected
    // quantity, remaining balance, and today's allowed allocation — always
    // derived live from the scheme rules + collection history, never a
    // stored mutable counter that could drift out of sync.
    Task<EntitlementSummaryDto> GetEntitlementAsync(int familyId);
}
