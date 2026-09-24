using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Qr;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Services.Qr;

public interface IQrScanService
{
    Task<QrScanResultDto> ScanAsync(string qrData);
}

// Single entry point for the global QR scanner (camera, image upload and
// manual entry all land here). Turns every validation outcome into a
// structured status instead of an HTTP error, so the scanner can show a
// specific, translated result screen. Distribution itself still goes through
// RationCollectionService, which re-validates everything atomically.
public class QrScanService(IBeneficiaryVerificationService verificationService) : IQrScanService
{
    public async Task<QrScanResultDto> ScanAsync(string qrData)
    {
        BeneficiaryVerificationResponseDto v;
        try
        {
            v = await verificationService.VerifyByQrAsync(qrData);
        }
        catch (ApiException ex) when (ex.ErrorCode is not null)
        {
            return new QrScanResultDto { Verified = false, Status = ex.ErrorCode, Message = ex.Message };
        }

        var summary = v.VerificationSummary;
        var ready = summary.OverallStatus == "READY_FOR_RATION_COLLECTION";

        var status = ready ? QrScanStatus.Verified : v.Booking.Status switch
        {
            nameof(TokenStatus.Completed) => QrScanStatus.AlreadyCollected,
            nameof(TokenStatus.Cancelled) => QrScanStatus.BookingCancelled,
            _ when IsPastCollectionDate(v.Booking.CollectionDate) => QrScanStatus.Expired,
            _ => QrScanStatus.NotEligible
        };

        return new QrScanResultDto
        {
            Verified = ready,
            Status = status,
            Message = ready ? "QR verified successfully" : summary.BlockedReason ?? "Collection is blocked.",
            TokenNumber = v.Booking.TokenNumber,
            Verification = v
        };
    }

    private static bool IsPastCollectionDate(string collectionDate) =>
        DateTime.TryParse(collectionDate, out var date) && date.Date < DateTime.UtcNow.Date;
}
