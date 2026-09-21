using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Models;

namespace SmartRation.Api.Mapping;

public static class TokenMappingExtensions
{
    public static TokenDto ToDto(this Token token) => new()
    {
        Id = token.Id,
        TokenNumber = token.TokenNumber,
        Status = token.Status.ToString(),
        UserId = token.UserId,
        UserName = token.User?.FullName ?? string.Empty,
        RationShopId = token.RationShopId,
        RationShopName = token.RationShop?.ShopName ?? string.Empty,
        TimeSlotId = token.TimeSlotId,
        SlotDate = token.TimeSlot?.SlotDate ?? default,
        StartTime = token.TimeSlot?.StartTime ?? default,
        EndTime = token.TimeSlot?.EndTime ?? default,
        QRCodeValue = token.QRCodeValue,
        Items = token.Items.Select(i => new TokenItemDto
        {
            RationType = i.RationType.ToString(),
            Quantity = i.Quantity
        }).ToList(),
        CreatedAt = token.CreatedAt,
        CollectedAt = token.CollectedAt
    };
}
