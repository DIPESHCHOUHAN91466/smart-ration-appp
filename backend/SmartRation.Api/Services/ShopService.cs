using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.DTOs.Shop;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Services;

public class ShopService(
    SmartRationDbContext db,
    ICurrentUserService currentUser,
    IRationCollectionService collectionService) : IShopService
{
    public async Task<ShopDashboardDto> GetDashboardAsync()
    {
        var shopId = RequireShopId();

        var shop = await db.RationShops.FirstOrDefaultAsync(s => s.Id == shopId)
            ?? throw new NotFoundException("Ration shop not found.");

        var today = DateTime.UtcNow.Date;

        var todaysTokens = await db.Tokens
            .Where(t => t.RationShopId == shopId && t.TimeSlot.SlotDate.Date == today)
            .Select(t => t.Status)
            .ToListAsync();

        var inventory = await db.Inventory
            .Where(i => i.RationShopId == shopId)
            .OrderBy(i => i.RationType)
            .ToListAsync();

        return new ShopDashboardDto
        {
            ShopId = shop.Id,
            ShopName = shop.ShopName,
            TodayTotalTokens = todaysTokens.Count,
            TodayCompleted = todaysTokens.Count(s => s == TokenStatus.Completed),
            TodayPending = todaysTokens.Count(s => s is TokenStatus.Pending or TokenStatus.Confirmed),
            TodayCancelled = todaysTokens.Count(s => s == TokenStatus.Cancelled),
            Inventory = inventory.Select(i => i.ToDto()).ToList()
        };
    }

    public async Task<TokenDto> CompleteCollectionAsync(int tokenId, string? idempotencyKey = null)
    {
        var shopId = RequireShopId();

        var token = await db.Tokens
            .Include(t => t.User)
            .Include(t => t.RationShop)
            .Include(t => t.TimeSlot)
            .Include(t => t.Items)
            .FirstOrDefaultAsync(t => t.Id == tokenId)
            ?? throw new NotFoundException("Token not found.");

        if (currentUser.Role == UserRole.ShopOwner && token.RationShopId != shopId)
        {
            throw new ForbiddenException("This token belongs to a different ration shop.");
        }

        // Token status (used / cancelled / expired) is checked by the shared
        // pipeline, AFTER it honours an idempotent replay of this same request.

        // Kept for API compatibility, but no longer a separate, weaker path:
        // it runs the exact same authoritative pipeline as QR verification
        // (eligibility, entitlement, token validity, all-or-nothing stock,
        // ledger, audit, receipt) inside one transaction.
        await collectionService.ConfirmCollectionAsync(token.Id, "QUEUE", idempotencyKey);

        var completed = await db.Tokens
            .Include(t => t.User)
            .Include(t => t.RationShop)
            .Include(t => t.TimeSlot)
            .Include(t => t.Items)
            .FirstAsync(t => t.Id == tokenId);
        return completed.ToDto();
    }

    private int RequireShopId()
    {
        if (currentUser.Role == UserRole.ShopOwner)
        {
            return currentUser.RationShopId
                ?? throw new BadRequestException("Your account is not linked to a ration shop.");
        }

        throw new ForbiddenException("Only shop owners can access this resource.");
    }
}
