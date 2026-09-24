namespace SmartRation.Api.Models;

public enum NotificationType
{
    BookingConfirmed = 1,
    TokenGenerated = 2,
    SlotReminder = 3,
    CollectionCompleted = 4,
    BookingCancelled = 5,
    LowInventory = 6,
    VerificationResult = 7,
    AIAlert = 8,
    SystemAnnouncement = 9
}

public class Notification
{
    public int Id { get; set; }

    public int UserId { get; set; }

    public User User { get; set; } = null!;

    public NotificationType Type { get; set; }

    public string Title { get; set; } = string.Empty;

    public string Message { get; set; } = string.Empty;

    public bool IsRead { get; set; } = false;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
