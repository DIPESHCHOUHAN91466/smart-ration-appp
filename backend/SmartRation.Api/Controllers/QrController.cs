using Microsoft.AspNetCore.RateLimiting;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Qr;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Qr;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/qr")]
[Authorize]
public class QrController(IQrService qrService, IQrScanService qrScanService) : ControllerBase
{
    [HttpPost("generate")]
    [Authorize(Roles = nameof(UserRole.RuralUser))]
    public async Task<ActionResult<ApiResponse<string>>> Generate(GenerateQrRequestDto request)
    {
        var value = await qrService.RegenerateForTokenAsync(request.TokenId);
        return Ok(ApiResponse<string>.Ok(value, "QR code ready"));
    }

    [HttpPost("verify")]
    [EnableRateLimiting("scan")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<TokenDto>>> Verify(VerifyQrRequestDto request)
    {
        var result = await qrService.VerifyAsync(request.QrCodeValue);
        return Ok(ApiResponse<TokenDto>.Ok(result, "QR code verified"));
    }

    // Signed JSON envelope for the caller's own token, rendered as the QR image
    // on "My Token & QR". Signing happens here so the secret never reaches the browser.
    [HttpGet("payload/{tokenId:int}")]
    [Authorize(Roles = $"{nameof(UserRole.RuralUser)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<string>>> Payload(int tokenId)
    {
        var payload = await qrService.GetPayloadForTokenAsync(tokenId);
        return Ok(ApiResponse<string>.Ok(payload, "QR payload ready"));
    }

    // Global scanner endpoint: camera scans, uploaded QR images and manual
    // entry all use this one pipeline. Validation outcomes come back as a
    // structured Status (200), not as HTTP errors.
    [HttpPost("scan")]
    [EnableRateLimiting("scan")]
    [Authorize(Roles = nameof(UserRole.ShopOwner))]
    public async Task<ActionResult<ApiResponse<QrScanResultDto>>> Scan(QrScanRequestDto request)
    {
        var result = await qrScanService.ScanAsync(request.QrData);
        return Ok(ApiResponse<QrScanResultDto>.Ok(result, result.Message));
    }
}
