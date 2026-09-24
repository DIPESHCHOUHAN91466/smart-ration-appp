using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
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
    SmartRationDbContext db,
    ICurrentUserService currentUser) : ControllerBase
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

    [HttpGet("history/{beneficiaryId:int}")]
    public async Task<ActionResult<ApiResponse<List<CollectionHistoryItemDto>>>> History(int beneficiaryId)
    {
        var beneficiary = await db.Beneficiaries.FirstOrDefaultAsync(b => b.Id == beneficiaryId)
            ?? throw new NotFoundException("Beneficiary not found.");

        var allowed = currentUser.Role switch
        {
            UserRole.RuralUser => beneficiary.UserId == currentUser.UserId,
            UserRole.ShopOwner or UserRole.GovernmentOfficial or UserRole.Admin => true,
            _ => false
        };

        if (!allowed)
        {
            throw new ForbiddenException("You do not have access to this beneficiary's history.");
        }

        var collections = await db.RationCollections
            .Include(c => c.Items)
            .Include(c => c.RationShop)
            .Where(c => c.BeneficiaryId == beneficiaryId)
            .OrderByDescending(c => c.CollectedAt)
            .ToListAsync();

        var result = collections.Select(c => new CollectionHistoryItemDto
        {
            CollectionCode = c.CollectionCode,
            CollectedAt = c.CollectedAt.ToString("yyyy-MM-dd HH:mm"),
            ShopName = c.RationShop.ShopName,
            Items = c.Items.Select(i => new CollectedItemDto { RationType = i.RationType.ToString(), Quantity = i.Quantity }).ToList()
        }).ToList();

        return Ok(ApiResponse<List<CollectionHistoryItemDto>>.Ok(result));
    }
}
