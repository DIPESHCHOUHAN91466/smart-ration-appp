using SmartRation.Api.DTOs.Slots;

namespace SmartRation.Api.Services;

public interface ISlotService
{
    Task<IReadOnlyList<TimeSlotDto>> GetSlotsAsync(int shopId, DateTime date);

    Task<TimeSlotDto> CreateSlotAsync(CreateSlotRequestDto request);

    Task<TimeSlotDto> UpdateSlotAsync(int id, UpdateSlotRequestDto request);
}
