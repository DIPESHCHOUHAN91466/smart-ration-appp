using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

// DEMO/SYNTHETIC MODE — no real ration-passbook registry exists yet.
public class SyntheticPassbookVerificationService(SmartRationDbContext db) : IPassbookVerificationService
{
    public async Task<PassbookVerification> GetOrCreateAsync(int beneficiaryId)
    {
        var existing = await db.PassbookVerifications.FirstOrDefaultAsync(p => p.BeneficiaryId == beneficiaryId);
        if (existing is not null)
        {
            return existing;
        }

        var record = new PassbookVerification
        {
            BeneficiaryId = beneficiaryId,
            PassbookNumber = $"PB-DEMO-{beneficiaryId:D4}",
            Status = "ACTIVE",
            VerificationStatus = PassbookVerificationStatus.Verified,
            LastUpdated = DateTime.UtcNow,
            VerificationSource = "SYNTHETIC_DEMO"
        };

        db.PassbookVerifications.Add(record);
        await db.SaveChangesAsync();
        return record;
    }
}
