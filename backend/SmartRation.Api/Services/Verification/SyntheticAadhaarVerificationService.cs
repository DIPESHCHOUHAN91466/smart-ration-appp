using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

// DEMO/SYNTHETIC MODE — never a real Aadhaar eKYC call. Reads the
// beneficiary's stored (seeded or previously-provisioned) verification
// record, or provisions a pre-verified synthetic one if missing.
public class SyntheticAadhaarVerificationService(SmartRationDbContext db) : IAadhaarVerificationService
{
    public async Task<AadhaarVerification> GetOrCreateAsync(int beneficiaryId)
    {
        var existing = await db.AadhaarVerifications.FirstOrDefaultAsync(a => a.BeneficiaryId == beneficiaryId);
        if (existing is not null)
        {
            return existing;
        }

        var lastFour = ((beneficiaryId * 6173) % 9000 + 1000).ToString();

        var record = new AadhaarVerification
        {
            BeneficiaryId = beneficiaryId,
            AadhaarReferenceId = $"AAD-DEMO-{beneficiaryId:D6}",
            AadhaarMasked = MaskingUtil.MaskSyntheticAadhaar(lastFour),
            Status = AadhaarVerificationStatus.Verified,
            VerificationDate = DateTime.UtcNow,
            VerificationSource = "SYNTHETIC_DEMO",
            VerificationMode = "PRE_VERIFIED"
        };

        db.AadhaarVerifications.Add(record);
        await db.SaveChangesAsync();
        return record;
    }
}
