using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public interface ICurrentUserService
{
    int UserId { get; }

    UserRole Role { get; }

    int? RationShopId { get; }
}
