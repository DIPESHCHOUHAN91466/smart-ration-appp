using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Services.Verification;

// The entitlement-aware collection-confirmation path used by the new
// beneficiary verification screen. Re-validates everything server-side
// (never trusts that nothing changed since the GET verification call),
// then atomically decrements inventory, completes the token, records the
// RationCollection receipt, and audits — all in one transaction. If
// inventory can't be decremented, the token is never marked collected.
public class RationCollectionService(
    SmartRationDbContext db,
    IBeneficiaryVerificationService verificationService,
    IEntitlementService entitlementService,
    ICurrentUserService currentUser,
    IAuditLogService auditLog,
    IVerificationAuditService verificationAudit,
    INotificationService notificationService,
    ILogger<RationCollectionService> logger) : IRationCollectionService
{
    public async Task<CollectionReceiptDto> ConfirmCollectionAsync(int tokenId, string verificationMethod, string? idempotencyKey = null)
    {
        // Low-bandwidth retry: the same key means "the request I already sent".
        // Return the original receipt instead of a confusing "already used" error.
        if (!string.IsNullOrEmpty(idempotencyKey))
        {
            var previous = await db.RationCollections
                .Include(c => c.Items)
                .Include(c => c.RationShop)
                .Include(c => c.Token)
                .Include(c => c.Beneficiary).ThenInclude(b => b.Family).ThenInclude(f => f.RationScheme)
                .Include(c => c.Beneficiary).ThenInclude(b => b.Family).ThenInclude(f => f.Members)
                .Include(c => c.Beneficiary).ThenInclude(b => b.User)
                .FirstOrDefaultAsync(c => c.IdempotencyKey == idempotencyKey);

            if (previous is not null)
            {
                if (previous.TokenId != tokenId || previous.OperatorUserId != currentUser.UserId)
                {
                    throw new ConflictException("This request key was already used for a different collection.") { ErrorCode = "IDEMPOTENCY_KEY_REUSED" };
                }
                return ToReceipt(previous);
            }
        }

        // Re-runs every check (Aadhaar/passbook/mobile/token/family/entitlement)
        // fresh — this is the authoritative gate, not the earlier GET call.
        var verification = await verificationService.BuildResponseForTokenAsync(tokenId, verificationMethod);

        var token = await db.Tokens
            .Include(t => t.Items)
            .Include(t => t.RationShop)
            .FirstOrDefaultAsync(t => t.Id == tokenId)
            ?? throw new NotFoundException("Booking not found.");

        if (currentUser.Role == UserRole.ShopOwner && token.RationShopId != currentUser.RationShopId)
        {
            throw new ForbiddenException("This booking belongs to a different ration shop.");
        }

        if (verification.VerificationSummary.OverallStatus != "READY_FOR_RATION_COLLECTION")
        {
            await verificationAudit.LogAsync(
                VerificationAction.CollectionRejected, "BLOCKED", verificationMethod,
                tokenNumber: token.TokenNumber, beneficiaryId: verification.Beneficiary.Id, shopId: token.RationShopId,
                reason: verification.VerificationSummary.BlockedReason);

            throw new ConflictException(verification.VerificationSummary.BlockedReason ?? "Collection is blocked.");
        }

        var requested = token.Items.Where(i => i.Quantity > 0).ToList();
        if (requested.Count == 0)
        {
            throw new BadRequestException("This booking has no items to issue.") { ErrorCode = "NO_ITEMS" };
        }

        // Entitlement: the booked quantities must fit today's allowance in full.
        // Rejected outright (400) rather than silently issuing less.
        try
        {
            entitlementService.EnsureRequestWithinEntitlement(verification.Entitlement, requested.Select(i => (i.RationType, i.Quantity)));
        }
        catch (BadRequestException ex)
        {
            await verificationAudit.LogAsync(
                VerificationAction.CollectionRejected, "BLOCKED", verificationMethod,
                tokenNumber: token.TokenNumber, beneficiaryId: verification.Beneficiary.Id, shopId: token.RationShopId,
                reason: ex.Message);
            throw;
        }

        // Inventory: all-or-nothing. Every item must be fully in stock before
        // anything is deducted — no partial issue, never a negative balance.
        var stock = await db.Inventory
            .Where(i => i.RationShopId == token.RationShopId)
            .ToDictionaryAsync(i => i.RationType);
        var shortItem = requested.FirstOrDefault(i => !stock.TryGetValue(i.RationType, out var inv) || inv.AvailableQuantity < i.Quantity);
        if (shortItem is not null)
        {
            await verificationAudit.LogAsync(
                VerificationAction.CollectionRejected, "BLOCKED", verificationMethod,
                tokenNumber: token.TokenNumber, beneficiaryId: verification.Beneficiary.Id, shopId: token.RationShopId,
                reason: $"Insufficient {shortItem.RationType} stock.");
            throw new ConflictException($"Insufficient {shortItem.RationType} stock to complete this collection.") { ErrorCode = "INSUFFICIENT_STOCK" };
        }

        // Collection + stock deduction + ledger + audit commit together or not at all.
        await using var transaction = await db.Database.BeginTransactionAsync();

        var issuedItems = new List<RationCollectionItem>();
        foreach (var item in requested)
        {
            var inventory = stock[item.RationType];
            inventory.AvailableQuantity -= item.Quantity;
            inventory.AllocatedQuantity += item.Quantity;
            inventory.UpdatedAt = DateTime.UtcNow;
            InventoryLedger.Record(db, inventory, InventoryMovementType.Distributed, item.Quantity, currentUser.UserId, token.TokenNumber);

            issuedItems.Add(new RationCollectionItem { RationType = item.RationType, Quantity = item.Quantity });
        }

        token.Status = TokenStatus.Completed;
        token.CollectedAt = DateTime.UtcNow;

        var collection = new RationCollection
        {
            CollectionCode = string.Empty,
            TokenId = token.Id,
            BeneficiaryId = verification.Beneficiary.Id,
            RationShopId = token.RationShopId,
            OperatorUserId = currentUser.UserId,
            VerificationMethod = verificationMethod,
            IdempotencyKey = string.IsNullOrEmpty(idempotencyKey) ? null : idempotencyKey,
            CollectedAt = DateTime.UtcNow,
            Items = issuedItems
        };
        db.RationCollections.Add(collection);

        try
        {
            await db.SaveChangesAsync();
        }
        catch (DbUpdateException ex)
        {
            // Unique TokenId / IdempotencyKey, or Inventory's concurrency check:
            // someone else changed this token or this stock at the same moment.
            // Disposing the transaction rolls every change back.
            logger.LogWarning(ex, "Collection confirmation for token {TokenId} lost a concurrent update; rolled back.", tokenId);
            throw new ConflictException("Could not complete the collection due to a concurrent update. Please try again.") { ErrorCode = "CONCURRENT_UPDATE" };
        }

        collection.CollectionCode = $"COL-DEMO-{collection.Id:D6}";
        await db.SaveChangesAsync();

        await auditLog.LogAsync(currentUser.UserId, "COLLECTION_COMPLETED", nameof(Token), token.Id.ToString(), $"{token.TokenNumber} {collection.CollectionCode} via {verificationMethod}");
        await verificationAudit.LogAsync(
            VerificationAction.CollectionConfirmed, "SUCCESS", verificationMethod,
            tokenNumber: token.TokenNumber, beneficiaryId: verification.Beneficiary.Id, shopId: token.RationShopId);

        await transaction.CommitAsync();

        logger.LogInformation("Collection confirmed: {CollectionCode} for token {TokenNumber} via {Method}", collection.CollectionCode, token.TokenNumber, verificationMethod);

        await notificationService.CreateAsync(
            token.UserId,
            NotificationType.CollectionCompleted,
            "Ration collected",
            $"Your ration for token {token.TokenNumber} has been collected. Collection ID {collection.CollectionCode}.");

        return new CollectionReceiptDto
        {
            CollectionCode = collection.CollectionCode,
            TokenNumber = token.TokenNumber,
            BeneficiaryName = verification.Beneficiary.FullName,
            FamilySize = verification.Family.FamilySize,
            SchemeCode = verification.Entitlement.SchemeCode,
            IssuedItems = issuedItems.Select(i => new CollectedItemDto { RationType = i.RationType.ToString(), Quantity = i.Quantity }).ToList(),
            TotalQuantityKg = issuedItems.Sum(i => i.Quantity),
            ShopName = token.RationShop.ShopName,
            CollectedAt = collection.CollectedAt.ToString("yyyy-MM-dd HH:mm")
        };
    }

    private static CollectionReceiptDto ToReceipt(RationCollection c) => new()
    {
        CollectionCode = c.CollectionCode,
        TokenNumber = c.Token.TokenNumber,
        BeneficiaryName = c.Beneficiary.User?.FullName ?? string.Empty,
        FamilySize = c.Beneficiary.Family?.Members.Count ?? 0,
        SchemeCode = c.Beneficiary.Family?.RationScheme?.SchemeCode ?? string.Empty,
        IssuedItems = c.Items.Select(i => new CollectedItemDto { RationType = i.RationType.ToString(), Quantity = i.Quantity }).ToList(),
        TotalQuantityKg = c.Items.Sum(i => i.Quantity),
        ShopName = c.RationShop.ShopName,
        CollectedAt = c.CollectedAt.ToString("yyyy-MM-dd HH:mm")
    };
}
