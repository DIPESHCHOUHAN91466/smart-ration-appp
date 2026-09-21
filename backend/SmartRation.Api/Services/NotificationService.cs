using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Notifications;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public class NotificationService(SmartRationDbContext db, ICurrentUserService currentUser) : INotificationService
{
    public async Task CreateAsync(int userId, NotificationType type, string title, string message)
    {
        db.Notifications.Add(new Notification
        {
            UserId = userId,
            Type = type,
            Title = title,
            Message = message
        });

        await db.SaveChangesAsync();
    }

    public async Task<IReadOnlyList<NotificationDto>> GetForCurrentUserAsync()
    {
        return await db.Notifications
            .Where(n => n.UserId == currentUser.UserId)
            .OrderByDescending(n => n.CreatedAt)
            .Select(n => new NotificationDto
            {
                Id = n.Id,
                Type = n.Type.ToString(),
                Title = n.Title,
                Message = n.Message,
                IsRead = n.IsRead,
                CreatedAt = n.CreatedAt
            })
            .ToListAsync();
    }

    public async Task MarkReadAsync(IReadOnlyList<int> notificationIds)
    {
        var notifications = await db.Notifications
            .Where(n => n.UserId == currentUser.UserId && notificationIds.Contains(n.Id))
            .ToListAsync();

        foreach (var notification in notifications)
        {
            notification.IsRead = true;
        }

        await db.SaveChangesAsync();
    }
}
