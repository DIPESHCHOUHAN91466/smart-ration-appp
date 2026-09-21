using SmartRation.Api.DTOs.Notifications;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public interface INotificationService
{
    Task CreateAsync(int userId, NotificationType type, string title, string message);

    Task<IReadOnlyList<NotificationDto>> GetForCurrentUserAsync();

    Task MarkReadAsync(IReadOnlyList<int> notificationIds);
}
