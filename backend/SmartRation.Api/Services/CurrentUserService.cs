using System.Security.Claims;
using SmartRation.Api.Common;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public class CurrentUserService(IHttpContextAccessor httpContextAccessor) : ICurrentUserService
{
    private ClaimsPrincipal? Principal => httpContextAccessor.HttpContext?.User;

    public int UserId
    {
        get
        {
            var value = Principal?.FindFirstValue(ClaimTypes.NameIdentifier)
                ?? Principal?.FindFirstValue("sub");

            if (value is null || !int.TryParse(value, out var userId))
            {
                throw new UnauthorizedApiException("No authenticated user found on the request.");
            }

            return userId;
        }
    }

    public UserRole Role
    {
        get
        {
            var value = Principal?.FindFirstValue(ClaimTypes.Role);
            if (value is null || !Enum.TryParse<UserRole>(value, out var role))
            {
                throw new UnauthorizedApiException("No authenticated user role found on the request.");
            }

            return role;
        }
    }

    public int? RationShopId
    {
        get
        {
            var value = Principal?.FindFirstValue("rationShopId");
            return value is not null && int.TryParse(value, out var shopId) ? shopId : null;
        }
    }
}
