using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Users;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

// The signed-in user's own account (UsersController) and the staff user list (AdminController).
public interface IUserAccountService
{
    Task<UserSummaryDto> GetOwnProfileAsync();
    Task<UserSummaryDto> UpdateOwnProfileAsync(UpdateProfileRequestDto request);
    Task<List<UserSummaryDto>> ListUsersAsync(string? role);
}

public class UserAccountService(SmartRationDbContext db, ICurrentUserService currentUser) : IUserAccountService
{
    public async Task<UserSummaryDto> GetOwnProfileAsync() => (await LoadOwnAsync()).ToSummaryDto();

    public async Task<UserSummaryDto> UpdateOwnProfileAsync(UpdateProfileRequestDto request)
    {
        var user = await LoadOwnAsync();
        // Check the value that will be SAVED (trimmed). Checking the raw input let " 9000000051" pass
        // and then fail on the unique index as a 500 instead of this 409.
        var mobile = request.MobileNumber.Trim();
        var mobileTaken = await db.Users.AnyAsync(u => u.MobileNumber == mobile && u.Id != user.Id);
        if (mobileTaken)
        {
            throw new ConflictException("Another account already uses this mobile number.");
        }

        user.FullName = request.FullName.Trim();
        user.MobileNumber = mobile;
        await db.SaveChangesAsync();
        return user.ToSummaryDto();
    }

    public async Task<List<UserSummaryDto>> ListUsersAsync(string? role)
    {
        var query = db.Users.AsQueryable();
        if (!string.IsNullOrWhiteSpace(role))
        {
            if (!Enum.TryParse<UserRole>(role, ignoreCase: true, out var parsedRole))
            {
                throw new BadRequestException($"Unknown role '{role}'.");
            }
            query = query.Where(u => u.Role == parsedRole);
        }
        var users = await query.OrderBy(u => u.FullName).ToListAsync();
        return users.Select(u => u.ToSummaryDto()).ToList();
    }

    private async Task<User> LoadOwnAsync() =>
        await db.Users.FirstOrDefaultAsync(u => u.Id == currentUser.UserId)
        ?? throw new NotFoundException("User profile not found.");
}
