using SmartRation.Api.DTOs.Verification;

namespace SmartRation.Api.Services.Verification;

public interface IBeneficiaryVerificationService
{
    Task<BeneficiaryVerificationResponseDto> VerifyByQrAsync(string qrValue);

    // Used by the OTP fallback once a mobile OTP has been verified — finds
    // the beneficiary's relevant active booking at the requesting shop and
    // returns the exact same consolidated profile the QR path would.
    Task<BeneficiaryVerificationResponseDto> VerifyByBeneficiaryAtShopAsync(int beneficiaryId, int shopId, string verificationMethod);

    Task<BeneficiaryVerificationResponseDto> BuildResponseForTokenAsync(int tokenId, string verificationMethod);
}
