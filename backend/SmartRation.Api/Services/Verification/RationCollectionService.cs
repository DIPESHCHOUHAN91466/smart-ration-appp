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
    ICurrentUserService currentUser,
    IAuditLogService auditLog,
    IVerificationAuditService verificationAudit,
    INotificationService notificationService,
    ILogger<RationCollectionService> logger) : IRationCollectionService
{
    public async Task<CollectionReceiptDto> ConfirmCollectionAsync(int tokenId, string verificationMethod)
    {
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

        var entitlementByType = verification.Entitlement.Items.ToDictionary(i => i.RationType, i => i.TodayAllocation);

        await using var transaction = await db.Database.BeginTransactionAsync();

        var issuedItems = new List<RationCollectionItem>();

        foreach (var tokenItem in token.Items)
        {
            var rationTypeName = tokenItem.RationType.ToString();
            var entitlementCap = entitlementByType.GetValueOrDefault(rationTypeName, 0m);

            var inventory = await db.Inventory.FirstOrDefaultAsync(i => i.RationShopId == token.RationShopId && i.RationType == tokenItem.RationType);
            var inventoryCap = inventory?.AvailableQuantity ?? 0m;

            var issueQuantity = new[] { tokenItem.Quantity, entitlementCap, inventoryCap }.Min();
            if (issueQuantity <= 0)
            {
                continue;
            }

            if (inventory is null)
            {
                throw new ConflictException($"Insufficient {tokenItem.RationType} stock to complete this collection.");
            }

            inventory.AvailableQuantity -= issueQuantity;
            inventory.AllocatedQuantity += issueQuantity;
            inventory.UpdatedAt = DateTime.UtcNow;

            issuedItems.Add(new RationCollectionItem { RationType = tokenItem.RationType, Quantity = issueQuantity });
        }

        if (issuedItems.Count == 0)
        {
            await verificationAudit.LogAsync(
                VerificationAction.CollectionRejected, "BLOCKED", verificationMethod,
                tokenNumber: token.TokenNumber, beneficiaryId: verification.Beneficiary.Id, shopId: token.RationShopId,
                reason: "Insufficient shop inventory.");

            throw new ConflictException("Insufficient shop inventory to complete this collection.");
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
            CollectedAt = DateTime.UtcNow,
            Items = issuedItems
        };
        db.RationCollections.Add(collection);

        try
        {
            await db.SaveChangesAsync();
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Collection confirmation failed for token {TokenId}; inventory will not be decremented.", tokenId);
            throw new ConflictException("Could not complete the collection due to a stock update conflict. Please try again.");
        }

        collection.CollectionCode = $"COL-DEMO-{collection.Id:D6}";
        await db.SaveChangesAsync();

        await transaction.CommitAsync();

        logger.LogInformation("Collection confirmed: {CollectionCode} for token {TokenNumber} via {Method}", collection.CollectionCode, token.TokenNumber, verificationMethod);

        await auditLog.LogAsync(currentUser.UserId, "COLLECTION_COMPLETED", nameof(Token), token.Id.ToString(), token.TokenNumber);
        await verificationAudit.LogAsync(
            VerificationAction.CollectionConfirmed, "SUCCESS", verificationMethod,
            tokenNumber: token.TokenNumber, beneficiaryId: verification.Beneficiary.Id, shopId: token.RationShopId);

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
}
