using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Users;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

// The signed-in user's own account. Logic: UserAccountService.
[ApiController]
[Route("api/users")]
[Authorize]
public class UsersController(IUserAccountService accounts) : ControllerBase
{
    [HttpGet("profile")]
    public async Task<ActionResult<ApiResponse<UserSummaryDto>>> GetProfile() =>
        Ok(ApiResponse<UserSummaryDto>.Ok(await accounts.GetOwnProfileAsync()));

    [HttpPut("profile")]
    public async Task<ActionResult<ApiResponse<UserSummaryDto>>> UpdateProfile(UpdateProfileRequestDto request) =>
        Ok(ApiResponse<UserSummaryDto>.Ok(await accounts.UpdateOwnProfileAsync(request), "Profile updated"));
}
