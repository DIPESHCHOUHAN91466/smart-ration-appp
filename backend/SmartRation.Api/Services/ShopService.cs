using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.DTOs.Shop;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public class ShopService(
    SmartRationDbContext db,
    ICurrentUserService currentUser,
    IAuditLogService auditLog,
    INotificationService notificationService) : IShopService
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

    public async Task<TokenDto> CompleteCollectionAsync(int tokenId)
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

        if (token.Status != TokenStatus.Confirmed)
        {
            throw new BadRequestException($"Cannot complete collection for a token in {token.Status} status.");
        }

        foreach (var item in token.Items)
        {
            var inventory = await db.Inventory.FirstOrDefaultAsync(i => i.RationShopId == token.RationShopId && i.RationType == item.RationType);
            if (inventory is null || inventory.AvailableQuantity < item.Quantity)
            {
                throw new ConflictException($"Insufficient {item.RationType} stock to complete this collection. Please reconcile inventory first.");
            }

            inventory.AvailableQuantity -= item.Quantity;
            inventory.AllocatedQuantity += item.Quantity;
            inventory.UpdatedAt = DateTime.UtcNow;
        }

        token.Status = TokenStatus.Completed;
        token.CollectedAt = DateTime.UtcNow;

        await db.SaveChangesAsync();

        await auditLog.LogAsync(currentUser.UserId, "COLLECTION_COMPLETED", nameof(Token), token.Id.ToString(), token.TokenNumber);
        await notificationService.CreateAsync(
            token.UserId,
            NotificationType.CollectionCompleted,
            "Ration collected",
            $"Your ration for token {token.TokenNumber} has been marked as collected. Thank you.");

        return token.ToDto();
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
