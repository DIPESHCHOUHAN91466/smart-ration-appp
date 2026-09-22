using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

// Creates the Family + FamilyMember(head) + Beneficiary + synthetic
// verification records for a newly registered rural user, so the
// verification/entitlement flow works immediately without any manual
// backend setup.
public interface IBeneficiaryProvisioningService
{
    Task<Beneficiary> ProvisionAsync(User user, int? rationShopId = null, int? rationSchemeId = null, string? address = null);
}
