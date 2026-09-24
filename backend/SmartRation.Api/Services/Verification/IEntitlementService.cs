using SmartRation.Api.Models;
using SmartRation.Api.DTOs.Verification;

namespace SmartRation.Api.Services.Verification;

public interface IEntitlementService
{
    // Recalculates monthly entitlement, this-month's already-collected
    // quantity, remaining balance, and today's allowed allocation — always
    // derived live from the scheme rules + collection history, never a
    // stored mutable counter that could drift out of sync.
    Task<EntitlementSummaryDto> GetEntitlementAsync(int familyId);

    // The single authoritative quantity check used by EVERY collection path
    // (QR verification and the shop queue's quick complete). Throws
    // BadRequestException (ENTITLEMENT_EXCEEDED) if any requested item is
    // above today's allowed allocation. Never trust client-side limits.
    void EnsureRequestWithinEntitlement(EntitlementSummaryDto entitlement, IEnumerable<(RationType Type, decimal Quantity)> requested);
}
