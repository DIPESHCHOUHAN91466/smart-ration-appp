using SmartRation.Api.DTOs.AI;

namespace SmartRation.Api.Services.AI;

public interface IAIIntelligenceService
{
    Task<AIIntelligenceCenterDto> GetIntelligenceCenterAsync();
}
