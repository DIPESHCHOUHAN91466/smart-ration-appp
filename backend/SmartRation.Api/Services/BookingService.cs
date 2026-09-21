using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Ration;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public class BookingService(
    SmartRationDbContext db,
    IQrService qrService,
    ICurrentUserService currentUser,
    IAuditLogService auditLog,
    INotificationService notificationService,
    ILogger<BookingService> logger) : IBookingService
{
    private static readonly TokenStatus[] ActiveStatuses = [TokenStatus.Pending, TokenStatus.Confirmed];

    public async Task<TokenDto> CreateBookingAsync(CreateBookingRequestDto request)
    {
        var shop = await db.RationShops.FirstOrDefaultAsync(s => s.Id == request.RationShopId && s.IsActive)
            ?? throw new NotFoundException("Ration shop not found or inactive.");

        var slot = await db.TimeSlots.FirstOrDefaultAsync(s => s.Id == request.TimeSlotId && s.RationShopId == request.RationShopId)
            ?? throw new NotFoundException("Time slot not found for this shop.");

        if (slot.SlotDate.Date < DateTime.UtcNow.Date)
        {
            throw new BadRequestException("Cannot book a time slot in the past.");
        }

        var duplicate = await db.Tokens.AnyAsync(t =>
            t.UserId == currentUser.UserId &&
            t.TimeSlotId == slot.Id &&
            ActiveStatuses.Contains(t.Status));

        if (duplicate)
        {
            throw new ConflictException("You already have an active booking for this time slot.");
        }

        var resolvedItems = await ResolveAndValidateItemsAsync(shop.Id, request.Items);

        if (slot.BookedCount >= slot.Capacity)
        {
            throw new ConflictException("This time slot is full. Please choose another slot.");
        }

        slot.BookedCount += 1;

        var token = new Token
        {
            TokenNumber = string.Empty,
            UserId = currentUser.UserId,
            RationShopId = shop.Id,
            TimeSlotId = slot.Id,
            Status = TokenStatus.Confirmed,
            CreatedAt = DateTime.UtcNow
        };

        db.Tokens.Add(token);

        try
        {
            await db.SaveChangesAsync();
        }
        catch (DbUpdateConcurrencyException)
        {
            throw new ConflictException("This time slot just became full. Please choose another slot.");
        }

        token.TokenNumber = $"SR-{token.CreatedAt:yyyy}-{token.Id:D6}";
        token.QRCodeValue = qrService.ComputeQrValue(token.Id, token.TokenNumber);

        foreach (var (type, quantity) in resolvedItems)
        {
            db.TokenItems.Add(new TokenItem { TokenId = token.Id, RationType = type, Quantity = quantity });
        }

        await db.SaveChangesAsync();

        logger.LogInformation("Booking created: token {TokenNumber} for user {UserId} at shop {ShopId}", token.TokenNumber, token.UserId, shop.Id);
        await auditLog.LogAsync(currentUser.UserId, "BOOKING_CREATED", nameof(Token), token.Id.ToString(), token.TokenNumber);
        await notificationService.CreateAsync(
            currentUser.UserId,
            NotificationType.TokenGenerated,
            "Ration token generated",
            $"Your token {token.TokenNumber} is confirmed for {slot.SlotDate:yyyy-MM-dd} at {slot.StartTime:hh\\:mm}.");

        return await GetBookingByIdAsync(token.Id);
    }

    public async Task<IReadOnlyList<TokenDto>> GetBookingsAsync()
    {
        var query = TokenQuery();

        query = currentUser.Role switch
        {
            UserRole.RuralUser => query.Where(t => t.UserId == currentUser.UserId),
            UserRole.ShopOwner => query.Where(t => t.RationShopId == currentUser.RationShopId),
            _ => query
        };

        var tokens = await query.OrderByDescending(t => t.CreatedAt).ToListAsync();
        return tokens.Select(t => t.ToDto()).ToList();
    }

    public async Task<TokenDto> GetBookingByIdAsync(int id)
    {
        var token = await TokenQuery().FirstOrDefaultAsync(t => t.Id == id)
            ?? throw new NotFoundException("Booking not found.");

        EnsureCanAccess(token);
        return token.ToDto();
    }

    public async Task<TokenDto> RescheduleBookingAsync(int id, int newTimeSlotId)
    {
        var token = await db.Tokens.Include(t => t.TimeSlot).FirstOrDefaultAsync(t => t.Id == id)
            ?? throw new NotFoundException("Booking not found.");

        EnsureCanAccess(token);

        if (token.Status != TokenStatus.Confirmed)
        {
            throw new BadRequestException($"Cannot reschedule a booking in {token.Status} status.");
        }

        var newSlot = await db.TimeSlots.FirstOrDefaultAsync(s => s.Id == newTimeSlotId && s.RationShopId == token.RationShopId)
            ?? throw new NotFoundException("Time slot not found for this shop.");

        if (newSlot.Id == token.TimeSlotId)
        {
            return token.ToDto();
        }

        if (newSlot.SlotDate.Date < DateTime.UtcNow.Date)
        {
            throw new BadRequestException("Cannot reschedule to a time slot in the past.");
        }

        if (newSlot.BookedCount >= newSlot.Capacity)
        {
            throw new ConflictException("The selected time slot is full.");
        }

        var oldSlot = token.TimeSlot;
        oldSlot.BookedCount = Math.Max(0, oldSlot.BookedCount - 1);
        newSlot.BookedCount += 1;
        token.TimeSlotId = newSlot.Id;

        try
        {
            await db.SaveChangesAsync();
        }
        catch (DbUpdateConcurrencyException)
        {
            throw new ConflictException("The selected time slot just became full. Please choose another slot.");
        }

        await auditLog.LogAsync(currentUser.UserId, "BOOKING_RESCHEDULED", nameof(Token), token.Id.ToString());

        return await GetBookingByIdAsync(token.Id);
    }

    public async Task CancelBookingAsync(int id)
    {
        var token = await db.Tokens.Include(t => t.TimeSlot).FirstOrDefaultAsync(t => t.Id == id)
            ?? throw new NotFoundException("Booking not found.");

        EnsureCanAccess(token);

        if (token.Status is TokenStatus.Completed or TokenStatus.Cancelled)
        {
            throw new BadRequestException($"Cannot cancel a booking that is already {token.Status}.");
        }

        token.Status = TokenStatus.Cancelled;
        token.TimeSlot.BookedCount = Math.Max(0, token.TimeSlot.BookedCount - 1);

        await db.SaveChangesAsync();

        await auditLog.LogAsync(currentUser.UserId, "BOOKING_CANCELLED", nameof(Token), token.Id.ToString());
        await notificationService.CreateAsync(
            token.UserId,
            NotificationType.BookingCancelled,
            "Booking cancelled",
            $"Your ration token {token.TokenNumber} has been cancelled.");
    }

    public async Task<IReadOnlyList<TokenDto>> GetTodayQueueForCurrentShopAsync()
    {
        if (currentUser.RationShopId is null)
        {
            throw new BadRequestException("Your account is not linked to a ration shop.");
        }

        var today = DateTime.UtcNow.Date;

        // SQLite can't ORDER BY a TimeSpan column, so sort client-side after materializing.
        var tokens = await TokenQuery()
            .Where(t => t.RationShopId == currentUser.RationShopId && t.TimeSlot.SlotDate.Date == today)
            .ToListAsync();

        return tokens.OrderBy(t => t.TimeSlot.StartTime).Select(t => t.ToDto()).ToList();
    }

    private IQueryable<Token> TokenQuery() =>
        db.Tokens
            .Include(t => t.User)
            .Include(t => t.RationShop)
            .Include(t => t.TimeSlot)
            .Include(t => t.Items)
            .AsQueryable();

    private void EnsureCanAccess(Token token)
    {
        var allowed = currentUser.Role switch
        {
            UserRole.RuralUser => token.UserId == currentUser.UserId,
            UserRole.ShopOwner => token.RationShopId == currentUser.RationShopId,
            UserRole.GovernmentOfficial or UserRole.Admin => true,
            _ => false
        };

        if (!allowed)
        {
            throw new ForbiddenException("You do not have access to this booking.");
        }
    }

    private async Task<List<(RationType Type, decimal Quantity)>> ResolveAndValidateItemsAsync(
        int shopId,
        List<DTOs.Ration.BookingItemRequestDto> items)
    {
        var resolved = new List<(RationType Type, decimal Quantity)>();

        foreach (var itemRequest in items)
        {
            if (!Enum.TryParse<RationType>(itemRequest.RationType, ignoreCase: true, out var rationType))
            {
                throw new BadRequestException($"Unknown ration item '{itemRequest.RationType}'.");
            }

            var catalogItem = await db.RationItems.FirstOrDefaultAsync(r => r.RationType == rationType && r.IsActive)
                ?? throw new BadRequestException($"'{itemRequest.RationType}' is not currently available.");

            if (itemRequest.Quantity <= 0 || itemRequest.Quantity > catalogItem.StandardQuotaPerBooking)
            {
                throw new BadRequestException(
                    $"Quantity for {catalogItem.Name} must be between 0 and the standard quota of {catalogItem.StandardQuotaPerBooking} {catalogItem.Unit}.");
            }

            var inventory = await db.Inventory.FirstOrDefaultAsync(i => i.RationShopId == shopId && i.RationType == rationType);
            if (inventory is null || inventory.AvailableQuantity < itemRequest.Quantity)
            {
                throw new BadRequestException($"Insufficient {catalogItem.Name} stock at this shop.");
            }

            resolved.Add((rationType, itemRequest.Quantity));
        }

        return resolved;
    }
}
