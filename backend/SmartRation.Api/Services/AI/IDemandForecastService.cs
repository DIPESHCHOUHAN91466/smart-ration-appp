using SmartRation.Api.DTOs.AI;

namespace SmartRation.Api.Services.AI;

// Rule-based statistical forecasting (trailing-30-day trend), not a trained
// ML model — deliberately simple and fully explainable given the size of
// the synthetic dataset. See the AI methodology note in the final report.
public interface IDemandForecastService
{
    Task<List<DemandForecastDto>> GetForecastAsync(int? shopId = null);
}
