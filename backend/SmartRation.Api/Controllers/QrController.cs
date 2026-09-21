using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Qr;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/qr")]
[Authorize]
public class QrController(IQrService qrService) : ControllerBase
{
    [HttpPost("generate")]
    [Authorize(Roles = nameof(UserRole.RuralUser))]
    public async Task<ActionResult<ApiResponse<string>>> Generate(GenerateQrRequestDto request)
    {
        var value = await qrService.RegenerateForTokenAsync(request.TokenId);
        return Ok(ApiResponse<string>.Ok(value, "QR code ready"));
    }

    [HttpPost("verify")]
    [Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
    public async Task<ActionResult<ApiResponse<TokenDto>>> Verify(VerifyQrRequestDto request)
    {
        var result = await qrService.VerifyAsync(request.QrCodeValue);
        return Ok(ApiResponse<TokenDto>.Ok(result, "QR code verified"));
    }
}
