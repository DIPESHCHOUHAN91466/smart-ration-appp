using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Services;

// The ration item list (RationController). With a shopId it adds each item's available shop
// stock (read-only; never the shop's minimum-stock level or other management fields). For a
// RuralUser caller it adds their own family's remaining entitlement this month (scheme and
// family-size driven, never a hardcoded universal quota).
public interface IRationCatalogService
{
    Task<List<RationItemDto>> GetItemsAsync(int? shopId);
}

public class RationCatalogService(SmartRationDbContext db, IEntitlementService entitlementService, ICurrentUserService currentUser) : IRationCatalogService
{
    public async Task<List<RationItemDto>> GetItemsAsync(int? shopId)
    {
        var items = await db.RationItems
            .Where(r => r.IsActive)
            .Select(r => new RationItemDto
            {
                Id = r.Id,
                RationType = r.RationType.ToString(),
                Name = r.Name,
                VernacularName = r.VernacularName,
                Unit = r.Unit,
                StandardQuotaPerBooking = r.StandardQuotaPerBooking
            })
            .ToListAsync();

        if (shopId.HasValue)
        {
            var stock = await db.Inventory
                .Where(i => i.RationShopId == shopId.Value)
                .ToDictionaryAsync(i => i.RationType.ToString(), i => i.AvailableQuantity);
            foreach (var item in items)
            {
                if (stock.TryGetValue(item.RationType, out var available))
                {
                    item.AvailableQuantity = available;
                }
            }
        }

        if (currentUser.Role == UserRole.RuralUser)
        {
            var familyId = await db.Beneficiaries
                .Where(b => b.UserId == currentUser.UserId)
                .Select(b => (int?)b.FamilyId)
                .FirstOrDefaultAsync();
            if (familyId.HasValue)
            {
                var entitlement = await entitlementService.GetEntitlementAsync(familyId.Value);
                var remaining = entitlement.Items.ToDictionary(i => i.RationType, i => i.Remaining);
                foreach (var item in items)
                {
                    if (remaining.TryGetValue(item.RationType, out var eligible))
                    {
                        item.EligibleQuantity = eligible;
                    }
                }
            }
        }

        return items;
    }
}
