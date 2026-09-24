using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

public class EntitlementService(SmartRationDbContext db) : IEntitlementService
{
    public async Task<EntitlementSummaryDto> GetEntitlementAsync(int familyId)
    {
        var family = await db.Families
            .Include(f => f.RationScheme).ThenInclude(s => s.EntitlementItems)
            .Include(f => f.Members)
            .Include(f => f.Beneficiaries)
            .FirstOrDefaultAsync(f => f.Id == familyId)
            ?? throw new NotFoundException("Family not found.");

        var eligibleMemberCount = family.Members.Count(m => m.Eligibility == EligibilityStatus.Eligible);
        var beneficiaryIds = family.Beneficiaries.Select(b => b.Id).ToList();

        var now = DateTime.UtcNow;
        var monthStart = new DateTime(now.Year, now.Month, 1, 0, 0, 0, DateTimeKind.Utc);
        var monthEnd = monthStart.AddMonths(1);

        // SQLite can't Sum a decimal column server-side (same limitation hit
        // in BookingService) — materialize the raw rows, then aggregate client-side.
        var collectedThisMonth = await db.RationCollectionItems
            .Where(ci =>
                beneficiaryIds.Contains(ci.RationCollection.BeneficiaryId) &&
                ci.RationCollection.CollectedAt >= monthStart &&
                ci.RationCollection.CollectedAt < monthEnd)
            .Select(ci => new { ci.RationType, ci.Quantity })
            .ToListAsync();

        var standardQuotas = await db.RationItems
            .Where(r => r.IsActive)
            .ToDictionaryAsync(r => r.RationType, r => r.StandardQuotaPerBooking);

        var items = new List<EntitlementItemDto>();

        foreach (var rule in family.RationScheme.EntitlementItems)
        {
            var monthlyEntitlement = rule.QuotaPerEligibleMemberPerMonth * eligibleMemberCount;
            var alreadyCollected = collectedThisMonth.Where(c => c.RationType == rule.RationType).Sum(c => c.Quantity);
            var remaining = Math.Max(0, monthlyEntitlement - alreadyCollected);
            var visitCap = standardQuotas.GetValueOrDefault(rule.RationType, remaining);
            var todayAllocation = Math.Min(remaining, visitCap);

            items.Add(new EntitlementItemDto
            {
                RationType = rule.RationType.ToString(),
                MonthlyEntitlement = monthlyEntitlement,
                AlreadyCollected = alreadyCollected,
                Remaining = remaining,
                TodayAllocation = todayAllocation
            });
        }

        return new EntitlementSummaryDto
        {
            SchemeCode = family.RationScheme.SchemeCode,
            SchemeName = family.RationScheme.Name,
            FamilySize = family.Members.Count,
            EligibleMemberCount = eligibleMemberCount,
            Items = items
        };
    }

    public void EnsureRequestWithinEntitlement(EntitlementSummaryDto entitlement, IEnumerable<(RationType Type, decimal Quantity)> requested)
    {
        var allowed = entitlement.Items.ToDictionary(i => i.RationType, i => i.TodayAllocation);

        foreach (var (type, quantity) in requested)
        {
            if (quantity < 0)
            {
                throw new BadRequestException("Requested quantity cannot be negative.") { ErrorCode = "INVALID_QUANTITY" };
            }

            // An item outside the scheme has an allowance of zero.
            if (quantity > allowed.GetValueOrDefault(type.ToString(), 0m))
            {
                throw new BadRequestException("Requested quantity exceeds the beneficiary entitlement.") { ErrorCode = "ENTITLEMENT_EXCEEDED" };
            }
        }
    }
}
