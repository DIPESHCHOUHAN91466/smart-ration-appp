using SmartRation.Api.DTOs.Ration;

namespace SmartRation.Api.Services;

public interface IBookingService
{
    Task<TokenDto> CreateBookingAsync(CreateBookingRequestDto request);

    Task<IReadOnlyList<TokenDto>> GetBookingsAsync();

    Task<TokenDto> GetBookingByIdAsync(int id);

    Task<TokenDto> RescheduleBookingAsync(int id, int newTimeSlotId);

    Task CancelBookingAsync(int id);

    Task<IReadOnlyList<TokenDto>> GetTodayQueueForCurrentShopAsync();
}
