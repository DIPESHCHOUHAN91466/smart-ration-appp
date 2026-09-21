using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Notifications;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

[ApiController]
[Route("api/notifications")]
[Authorize]
public class NotificationsController(INotificationService notificationService) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<ApiResponse<IReadOnlyList<NotificationDto>>>> GetNotifications()
    {
        var result = await notificationService.GetForCurrentUserAsync();
        return Ok(ApiResponse<IReadOnlyList<NotificationDto>>.Ok(result));
    }

    [HttpPost("read")]
    public async Task<ActionResult<ApiResponse<object?>>> MarkRead(MarkNotificationsReadRequestDto request)
    {
        await notificationService.MarkReadAsync(request.NotificationIds);
        return Ok(ApiResponse.Ok("Notifications marked as read"));
    }
}
