using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Users;
using SmartRation.Api.Mapping;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/users")]
[Authorize]
public class UsersController(SmartRationDbContext db, ICurrentUserService currentUser) : ControllerBase
{
    [HttpGet("profile")]
    public async Task<ActionResult<ApiResponse<UserSummaryDto>>> GetProfile()
    {
        var user = await db.Users.FirstOrDefaultAsync(u => u.Id == currentUser.UserId)
            ?? throw new NotFoundException("User profile not found.");

        return Ok(ApiResponse<UserSummaryDto>.Ok(user.ToSummaryDto()));
    }

    [HttpPut("profile")]
    public async Task<ActionResult<ApiResponse<UserSummaryDto>>> UpdateProfile(UpdateProfileRequestDto request)
    {
        var user = await db.Users.FirstOrDefaultAsync(u => u.Id == currentUser.UserId)
            ?? throw new NotFoundException("User profile not found.");

        var mobileTaken = await db.Users.AnyAsync(u => u.MobileNumber == request.MobileNumber && u.Id != user.Id);
        if (mobileTaken)
        {
            throw new ConflictException("Another account already uses this mobile number.");
        }

        user.FullName = request.FullName.Trim();
        user.MobileNumber = request.MobileNumber.Trim();
        await db.SaveChangesAsync();

        return Ok(ApiResponse<UserSummaryDto>.Ok(user.ToSummaryDto(), "Profile updated"));
    }
}
