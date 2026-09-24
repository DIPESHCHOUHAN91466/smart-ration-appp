using SmartRation.Api.DTOs.AI;

namespace SmartRation.Api.Services.AI;

public interface IBeneficiaryInsightService
{
    Task<BeneficiaryRiskInsightDto> GetBeneficiaryInsightAsync(int beneficiaryId);
}
