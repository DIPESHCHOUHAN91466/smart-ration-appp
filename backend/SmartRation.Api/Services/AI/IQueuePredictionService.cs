using SmartRation.Api.DTOs.AI;

namespace SmartRation.Api.Services.AI;

public interface IQueuePredictionService
{
    Task<List<QueuePredictionDto>> GetPredictionsAsync(int? shopId = null);
}
