namespace SmartRation.Api.Services;

public interface IAuditLogService
{
    Task LogAsync(int? userId, string action, string entityName, string? entityId = null, string? details = null, string result = "SUCCESS", string? role = null);
}
