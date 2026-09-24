using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Services.Verification;

public class BeneficiaryVerificationService(
    SmartRationDbContext db,
    IQrService qrService,
    IAadhaarVerificationService aadhaarService,
    IPassbookVerificationService passbookService,
    IEntitlementService entitlementService,
    IVerificationAuditService verificationAudit) : IBeneficiaryVerificationService
{
    public async Task<BeneficiaryVerificationResponseDto> VerifyByQrAsync(string qrValue)
    {
        Token token;
        try
        {
            token = await qrService.ResolveTokenForVerificationAsync(qrValue);
        }
        catch (ApiException ex)
        {
            await verificationAudit.LogAsync(VerificationAction.QrScanned, "FAILED", "QR", reason: ex.Message);
            throw;
        }

        // Log the opaque reference, never the raw scanned payload.
        await verificationAudit.LogAsync(VerificationAction.QrScanned, "SUCCESS", "QR", verificationReference: qrService.ParseScannedQr(qrValue).Reference, tokenNumber: token.TokenNumber);

        return await BuildResponseAsync(token, "QR");
    }

    public async Task<BeneficiaryVerificationResponseDto> VerifyByBeneficiaryAtShopAsync(int beneficiaryId, int shopId, string verificationMethod)
    {
        var beneficiaryUserId = await db.Beneficiaries
            .Where(b => b.Id == beneficiaryId)
            .Select(b => b.UserId)
            .FirstOrDefaultAsync();

        if (beneficiaryUserId == 0)
        {
            throw new NotFoundException("Beneficiary not found.");
        }

        var today = DateTime.UtcNow.Date;

        var candidates = await db.Tokens
            .Include(t => t.User)
            .Include(t => t.RationShop)
            .Include(t => t.TimeSlot)
            .Include(t => t.Items)
            .Where(t => t.UserId == beneficiaryUserId && t.RationShopId == shopId && t.Status == TokenStatus.Confirmed)
            .ToListAsync();

        var resolved = candidates
            .OrderBy(t => Math.Abs((t.TimeSlot.SlotDate.Date - today).Days))
            .FirstOrDefault()
            ?? throw new NotFoundException("No active booking was found for this beneficiary at your shop.");

        return await BuildResponseAsync(resolved, verificationMethod);
    }

    public async Task<BeneficiaryVerificationResponseDto> BuildResponseForTokenAsync(int tokenId, string verificationMethod)
    {
        var token = await db.Tokens
            .Include(t => t.User)
            .Include(t => t.RationShop)
            .Include(t => t.TimeSlot)
            .Include(t => t.Items)
            .FirstOrDefaultAsync(t => t.Id == tokenId)
            ?? throw new NotFoundException("Booking not found.");

        return await BuildResponseAsync(token, verificationMethod);
    }

    private async Task<BeneficiaryVerificationResponseDto> BuildResponseAsync(Token token, string verificationMethod)
    {
        var beneficiary = await db.Beneficiaries
            .Include(b => b.User)
            .Include(b => b.Family).ThenInclude(f => f.Members)
            .Include(b => b.MobileVerification)
            .FirstOrDefaultAsync(b => b.UserId == token.UserId)
            ?? throw new NotFoundException("This user does not have a beneficiary profile yet.");

        var aadhaar = await aadhaarService.GetOrCreateAsync(beneficiary.Id);
        await verificationAudit.LogAsync(VerificationAction.AadhaarStatusChecked, "SUCCESS", verificationMethod, beneficiaryId: beneficiary.Id, shopId: token.RationShopId);

        var passbook = await passbookService.GetOrCreateAsync(beneficiary.Id);
        await verificationAudit.LogAsync(VerificationAction.PassbookStatusChecked, "SUCCESS", verificationMethod, beneficiaryId: beneficiary.Id, shopId: token.RationShopId);

        var mobile = beneficiary.MobileVerification;
        if (mobile is null)
        {
            mobile = new MobileVerification
            {
                BeneficiaryId = beneficiary.Id,
                MobileMasked = MaskingUtil.MaskMobile(beneficiary.User.MobileNumber),
                Status = MobileVerificationStatus.NotVerified,
                VerificationSource = "SYNTHETIC_DEMO"
            };
            db.MobileVerifications.Add(mobile);
            await db.SaveChangesAsync();
        }

        var entitlement = await entitlementService.GetEntitlementAsync(beneficiary.FamilyId);

        var previousCollections = await db.RationCollections
            .Include(c => c.Items)
            .Include(c => c.RationShop)
            .Where(c => c.BeneficiaryId == beneficiary.Id)
            .OrderByDescending(c => c.CollectedAt)
            .Take(10)
            .ToListAsync();

        var booking = new BookingSummaryDto
        {
            TokenId = token.Id,
            TokenNumber = token.TokenNumber,
            Status = token.Status.ToString(),
            CollectionDate = token.TimeSlot.SlotDate.ToString("yyyy-MM-dd"),
            BookingTime = token.TimeSlot.StartTime.ToString(@"hh\:mm"),
            ShopId = token.RationShopId,
            ShopName = token.RationShop.ShopName,
            ShopCode = token.RationShop.ShopCode,
            CollectionCompleted = token.Status == TokenStatus.Completed
        };

        var summary = BuildVerificationSummary(beneficiary, token, aadhaar, passbook, mobile, entitlement);

        if (summary.OverallStatus == "COLLECTION_BLOCKED" && token.Status == TokenStatus.Completed)
        {
            await verificationAudit.LogAsync(VerificationAction.TokenAlreadyUsed, "BLOCKED", verificationMethod, tokenNumber: token.TokenNumber, beneficiaryId: beneficiary.Id, shopId: token.RationShopId, reason: summary.BlockedReason);
        }

        await verificationAudit.LogAsync(
            VerificationAction.BeneficiaryVerified,
            summary.OverallStatus == "READY_FOR_RATION_COLLECTION" ? "SUCCESS" : "BLOCKED",
            verificationMethod,
            tokenNumber: token.TokenNumber,
            beneficiaryId: beneficiary.Id,
            shopId: token.RationShopId,
            reason: summary.BlockedReason);

        return new BeneficiaryVerificationResponseDto
        {
            Beneficiary = beneficiary.ToDto(),
            Family = beneficiary.Family.ToDto(),
            AadhaarVerification = aadhaar.ToDto(),
            PassbookVerification = passbook.ToDto(),
            MobileVerification = mobile.ToDto(),
            Booking = booking,
            Entitlement = entitlement,
            PreviousCollections = previousCollections.Select(c => new CollectionHistoryItemDto
            {
                CollectionCode = c.CollectionCode,
                CollectedAt = c.CollectedAt.ToString("yyyy-MM-dd HH:mm"),
                ShopName = c.RationShop.ShopName,
                Items = c.Items.Select(i => new CollectedItemDto { RationType = i.RationType.ToString(), Quantity = i.Quantity }).ToList()
            }).ToList(),
            VerificationSummary = summary
        };
    }

    private static VerificationSummaryDto BuildVerificationSummary(
        Beneficiary beneficiary,
        Token token,
        AadhaarVerification aadhaar,
        PassbookVerification passbook,
        MobileVerification mobile,
        EntitlementSummaryDto entitlement)
    {
        var aadhaarVerified = aadhaar.Status == AadhaarVerificationStatus.Verified;
        var passbookVerified = passbook.VerificationStatus == PassbookVerificationStatus.Verified;
        var mobileVerified = mobile.Status == MobileVerificationStatus.Verified;
        var isPastCollectionWindow = token.TimeSlot.SlotDate.Date < DateTime.UtcNow.Date;
        var tokenValid = token.Status == TokenStatus.Confirmed && !isPastCollectionWindow;
        var familyEligible = entitlement.EligibleMemberCount > 0;
        var entitlementAvailable = entitlement.Items.Any(i => i.TodayAllocation > 0);

        var summary = new VerificationSummaryDto
        {
            AadhaarVerified = aadhaarVerified,
            PassbookVerified = passbookVerified,
            MobileVerified = mobileVerified,
            TokenValid = tokenValid,
            FamilyEligible = familyEligible,
            EntitlementAvailable = entitlementAvailable
        };

        string? reason = beneficiary switch
        {
            { IsBlocked: true } => "This beneficiary account is blocked.",
            { IsActive: false } => "This beneficiary account is not active.",
            _ when token.Status == TokenStatus.Completed => "This token has already been used for collection.",
            _ when token.Status == TokenStatus.Cancelled => "This booking was cancelled.",
            _ when isPastCollectionWindow => "This token has expired — the booked collection date has passed.",
            _ when !tokenValid => $"Token is not valid for collection (status: {token.Status}).",
            _ when aadhaar.Status == AadhaarVerificationStatus.Failed => "Aadhaar verification failed.",
            _ when aadhaar.Status == AadhaarVerificationStatus.Expired => "Aadhaar verification has expired.",
            _ when !aadhaarVerified => "Aadhaar verification is pending.",
            _ when !passbookVerified => "Passbook verification is pending.",
            _ when !mobileVerified => "Mobile OTP verification required.",
            _ when !familyEligible => "This beneficiary is not eligible under the selected scheme.",
            _ when !entitlementAvailable => "No remaining ration entitlement.",
            _ => null
        };

        summary.OverallStatus = reason is null ? "READY_FOR_RATION_COLLECTION" : "COLLECTION_BLOCKED";
        summary.BlockedReason = reason;

        return summary;
    }
}
