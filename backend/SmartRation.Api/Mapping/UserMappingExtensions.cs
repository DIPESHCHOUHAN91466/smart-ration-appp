using SmartRation.Api.DTOs.Users;
using SmartRation.Api.Models;

namespace SmartRation.Api.Mapping;

public static class UserMappingExtensions
{
    public static UserSummaryDto ToSummaryDto(this User user) => new()
    {
        Id = user.Id,
        FullName = user.FullName,
        Email = user.Email,
        MobileNumber = user.MobileNumber,
        Role = user.Role.ToString(),
        RationShopId = user.RationShopId
    };
}
