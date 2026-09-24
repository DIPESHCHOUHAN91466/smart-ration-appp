using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.AI;

namespace SmartRation.Api.Controllers;

// OPTIONAL document OCR (ration card / passbook photo) via the Python service.
// Output is a suggestion for an operator to confirm — never identity
// verification, never required for the QR workflow. Aadhaar/mobile numbers
// are masked by the AI service before they leave it; nothing is stored here.
[ApiController]
[Route("api/ocr")]
[Authorize(Roles = $"{nameof(UserRole.ShopOwner)},{nameof(UserRole.GovernmentOfficial)},{nameof(UserRole.Admin)}")]
public class OcrController(IPythonAiClient pythonAi, IAuditLogService auditLog, ICurrentUserService currentUser) : ControllerBase
{
    private const long MaxBytes = 5 * 1024 * 1024;
    private static readonly string[] AllowedTypes = ["image/png", "image/jpeg"];

    [HttpPost("extract")]
    [RequestSizeLimit(MaxBytes + 64 * 1024)]
    public async Task<ActionResult<ApiResponse<AiAnalyticsResponseDto>>> Extract(IFormFile file, CancellationToken ct)
    {
        if (file is null || file.Length == 0 || file.Length > MaxBytes || !AllowedTypes.Contains(file.ContentType))
        {
            throw new BadRequestException("Upload a PNG or JPEG image up to 5 MB.") { ErrorCode = "INVALID_IMAGE" };
        }

        using var buffer = new MemoryStream();
        await file.CopyToAsync(buffer, ct);
        var result = await pythonAi.PostAsync("/v1/ocr/extract", new { image_base64 = Convert.ToBase64String(buffer.ToArray()) }, ct);

        await auditLog.LogAsync(currentUser.UserId, "OCR_EXTRACT", "Document", details: $"bytes={file.Length}", result: result.Available ? "SUCCESS" : "FAILED");
        return Ok(ApiResponse<AiAnalyticsResponseDto>.Ok(ToDto(result)));
    }

    // Same masking + field extraction for text an operator typed or pasted.
    [HttpPost("parse-text")]
    public async Task<ActionResult<ApiResponse<AiAnalyticsResponseDto>>> ParseText(OcrTextRequestDto request, CancellationToken ct)
    {
        var result = await pythonAi.PostAsync("/v1/ocr/parse-text", new { text = request.Text }, ct);
        return Ok(ApiResponse<AiAnalyticsResponseDto>.Ok(ToDto(result)));
    }

    private static AiAnalyticsResponseDto ToDto(PythonAiResult r) => r.Available
        ? new AiAnalyticsResponseDto { Available = true, Source = "python-ai", Data = r.Data }
        : new AiAnalyticsResponseDto { Available = false, Source = "unavailable", ErrorCode = r.ErrorCode, Message = r.Message };
}

public class OcrTextRequestDto
{
    [Required]
    [MaxLength(5000)]
    public string Text { get; set; } = string.Empty;
}
