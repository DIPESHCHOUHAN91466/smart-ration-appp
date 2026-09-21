using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Notifications;

public class MarkNotificationsReadRequestDto
{
    [Required, MinLength(1)]
    public List<int> NotificationIds { get; set; } = [];
}
