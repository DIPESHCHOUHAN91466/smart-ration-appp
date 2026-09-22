using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/verification")]
[Authorize(Roles = nameof(UserRole.ShopOwner))]
public class VerificationController(
    IBeneficiaryVerificationService verificationService,
    IOtpService otpService,
    ICurrentUserService currentUser,
    SmartRationDbContext db,
    IOptions<DemoModeOptions> demoOptions) : ControllerBase
{
    [HttpGet("qr/{reference}")]
    public async Task<ActionResult<ApiResponse<BeneficiaryVerificationResponseDto>>> VerifyByQr(string reference)
    {
        var result = await verificationService.VerifyByQrAsync(reference);
        return Ok(ApiResponse<BeneficiaryVerificationResponseDto>.Ok(result, "Beneficiary verified"));
    }

    [HttpPost("otp/request")]
    public async Task<ActionResult<ApiResponse<OtpRequestResponseDto>>> RequestOtp(OtpRequestRequestDto request)
    {
        var beneficiaryId = await db.Beneficiaries
            .Where(b => b.User.MobileNumber == request.MobileNumber)
            .Select(b => (int?)b.Id)
            .FirstOrDefaultAsync()
            ?? throw new NotFoundException("No beneficiary is registered with this mobile number.");

        var otp = await otpService.RequestOtpAsync(beneficiaryId, currentUser.UserId);

        var response = new OtpRequestResponseDto
        {
            OtpVerificationId = otp.Id,
            MobileMasked = MaskingUtil.MaskMobile(request.MobileNumber),
            ExpiresInMinutes = (int)Math.Ceiling((otp.ExpiresAt - DateTime.UtcNow).TotalMinutes),
            DemoOtpValue = demoOptions.Value.DemoOtpEnabled ? demoOptions.Value.DemoOtpValue : null
        };

        return Ok(ApiResponse<OtpRequestResponseDto>.Ok(response, "OTP sent"));
    }

    [HttpPost("otp/verify")]
    public async Task<ActionResult<ApiResponse<BeneficiaryVerificationResponseDto>>> VerifyOtp(OtpVerifyRequestDto request)
    {
        var otp = await otpService.VerifyOtpAsync(request.OtpVerificationId, request.Code);

        var shopId = currentUser.RationShopId
            ?? throw new BadRequestException("Your account is not linked to a ration shop.");

        var result = await verificationService.VerifyByBeneficiaryAtShopAsync(otp.BeneficiaryId, shopId, "OTP");
        return Ok(ApiResponse<BeneficiaryVerificationResponseDto>.Ok(result, "OTP verified"));
    }
}
