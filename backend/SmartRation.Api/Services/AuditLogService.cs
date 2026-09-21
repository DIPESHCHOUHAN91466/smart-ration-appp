using SmartRation.Api.Data;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public class AuditLogService(SmartRationDbContext db, IHttpContextAccessor httpContextAccessor) : IAuditLogService
{
    public async Task LogAsync(int? userId, string action, string entityName, string? entityId = null, string? details = null)
    {
        db.AuditLogs.Add(new AuditLog
        {
            UserId = userId,
            Action = action,
            EntityName = entityName,
            EntityId = entityId,
            Details = details,
            IpAddress = httpContextAccessor.HttpContext?.Connection.RemoteIpAddress?.ToString(),
            CreatedAt = DateTime.UtcNow
        });

        await db.SaveChangesAsync();
    }
}
