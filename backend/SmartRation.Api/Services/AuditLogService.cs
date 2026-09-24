using SmartRation.Api.Data;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public class AuditLogService(SmartRationDbContext db, IHttpContextAccessor httpContextAccessor) : IAuditLogService
{
    public async Task LogAsync(int? userId, string action, string entityName, string? entityId = null, string? details = null, string result = "SUCCESS", string? role = null)
    {
        db.AuditLogs.Add(new AuditLog
        {
            UserId = userId,
            Action = action,
            EntityName = entityName,
            EntityId = entityId,
            Details = details,
            // Explicit role for actions before the JWT exists (login); otherwise from the token.
            Role = role ?? httpContextAccessor.HttpContext?.User.FindFirst(System.Security.Claims.ClaimTypes.Role)?.Value,
            Result = result,
            IpAddress = httpContextAccessor.HttpContext?.Connection.RemoteIpAddress?.ToString(),
            CreatedAt = DateTime.UtcNow
        });

        await db.SaveChangesAsync();
    }
}
