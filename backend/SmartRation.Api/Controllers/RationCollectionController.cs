using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/ration/collection")]
[Authorize]
public class RationCollectionController(
    IRationCollectionService collectionService,
    IBeneficiaryProfileService profiles) : ControllerBase
{
    [HttpPost("confirm")]
    [Authorize(Roles = nameof(UserRole.ShopOwner))]
    public async Task<ActionResult<ApiResponse<CollectionReceiptDto>>> Confirm(
        ConfirmCollectionRequestDto request,
        [FromHeader(Name = "Idempotency-Key")] string? idempotencyKey)
    {
        if (idempotencyKey is { Length: > 64 })
        {
            throw new BadRequestException("Idempotency-Key must be at most 64 characters.") { ErrorCode = "INVALID_IDEMPOTENCY_KEY" };
        }

        var result = await collectionService.ConfirmCollectionAsync(request.TokenId, request.VerificationMethod, idempotencyKey);
        return Ok(ApiResponse<CollectionReceiptDto>.Ok(result, "Ration collection confirmed"));
    }

    // Same access rule as the beneficiary profile (BeneficiaryAccess).
    [HttpGet("history/{beneficiaryId:int}")]
    public async Task<ActionResult<ApiResponse<List<CollectionHistoryItemDto>>>> History(int beneficiaryId) =>
        Ok(ApiResponse<List<CollectionHistoryItemDto>>.Ok(await profiles.GetCollectionHistoryAsync(beneficiaryId)));
}
