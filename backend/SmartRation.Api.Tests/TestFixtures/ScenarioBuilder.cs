using SmartRation.Api.Data;
using SmartRation.Api.Models;

namespace SmartRation.Api.Tests.TestFixtures;

public record BasicScenario(
    RationShop Shop,
    RationScheme Scheme,
    User BeneficiaryUser,
    Beneficiary Beneficiary,
    Family Family,
    TimeSlot Slot,
    Token Token);

// Builds the minimal consistent set of rows every verification/entitlement/
// collection test needs, with sensible defaults and a few knobs for the
// specific negative cases (unverified Aadhaar, already-completed token, etc).
public static class ScenarioBuilder
{
    private static int _mobileSequence;

    // Synthetic block 9098xxxxxx (see backend/SmartRation.Python/app/synthetic): unique per test run,
    // never a real subscriber's number, and the same sequence every run (no Random).
    public static string NextSyntheticMobile() => $"9098{Interlocked.Increment(ref _mobileSequence):D6}";

    public static BasicScenario SeedBasicScenario(
        SmartRationDbContext db,
        AadhaarVerificationStatus aadhaarStatus = AadhaarVerificationStatus.Verified,
        PassbookVerificationStatus passbookStatus = PassbookVerificationStatus.Verified,
        MobileVerificationStatus mobileStatus = MobileVerificationStatus.Verified,
        TokenStatus tokenStatus = TokenStatus.Confirmed,
        decimal riceQuotaPerMember = 5,
        decimal riceInventory = 100)
    {
        db.RationItems.Add(new RationItem { RationType = RationType.Rice, Name = "Rice", VernacularName = "Tandul", Unit = "kg", StandardQuotaPerBooking = 5 });
        db.RationItems.Add(new RationItem { RationType = RationType.Wheat, Name = "Wheat", VernacularName = "Gahu", Unit = "kg", StandardQuotaPerBooking = 5 });

        var shop = new RationShop { ShopName = "Test Shop", ShopCode = "SHOP-TEST-001", Address = "Test", District = "Test", State = "Test", Latitude = 21, Longitude = 79, IsActive = true };
        db.RationShops.Add(shop);
        db.SaveChanges();

        var scheme = new RationScheme { SchemeCode = "TEST-SCHEME", Name = "Test Scheme", Description = "Test", IsActive = true };
        db.RationSchemes.Add(scheme);
        db.SaveChanges();
        db.SchemeEntitlementItems.Add(new SchemeEntitlementItem { RationSchemeId = scheme.Id, RationType = RationType.Rice, QuotaPerEligibleMemberPerMonth = riceQuotaPerMember });
        db.SaveChanges();

        db.Inventory.Add(new Inventory { RationShopId = shop.Id, RationType = RationType.Rice, AvailableQuantity = riceInventory, AllocatedQuantity = 0, MinimumStockLevel = 10 });
        db.SaveChanges();

        var user = new User { FullName = "Test Beneficiary", Email = $"test{Guid.NewGuid():N}@example.com", MobileNumber = NextSyntheticMobile(), PasswordHash = "x", Role = UserRole.RuralUser, IsActive = true };
        db.Users.Add(user);
        db.SaveChanges();

        var family = new Family { FamilyCode = "FAM-TEST-0001", RationShopId = shop.Id, RationSchemeId = scheme.Id, DataSource = "SYNTHETIC_DEMO" };
        db.Families.Add(family);
        db.SaveChanges();

        db.FamilyMembers.Add(new FamilyMember { FamilyId = family.Id, FullName = user.FullName, Age = 30, Relationship = FamilyRelationship.Head, Eligibility = EligibilityStatus.Eligible, DataSource = "SYNTHETIC_DEMO" });
        db.SaveChanges();

        var beneficiary = new Beneficiary { BeneficiaryCode = "BEN-TEST-0001", Address = "Test Village", UserId = user.Id, FamilyId = family.Id, IsActive = true, IsBlocked = false, DataSource = "SYNTHETIC_DEMO" };
        db.Beneficiaries.Add(beneficiary);
        db.SaveChanges();

        db.AadhaarVerifications.Add(new AadhaarVerification { BeneficiaryId = beneficiary.Id, AadhaarReferenceId = "AAD-TEST-000001", AadhaarMasked = "XXXX-XXXX-0001", Status = aadhaarStatus, VerificationSource = "SYNTHETIC_DEMO", VerificationMode = "PRE_VERIFIED" });
        db.PassbookVerifications.Add(new PassbookVerification { BeneficiaryId = beneficiary.Id, PassbookNumber = "PB-TEST-0001", Status = "ACTIVE", VerificationStatus = passbookStatus, VerificationSource = "SYNTHETIC_DEMO" });
        db.MobileVerifications.Add(new MobileVerification { BeneficiaryId = beneficiary.Id, MobileMasked = "******0001", Status = mobileStatus, VerificationSource = "SYNTHETIC_DEMO" });
        db.SaveChanges();

        var slot = new TimeSlot { RationShopId = shop.Id, SlotDate = DateTime.UtcNow.Date, StartTime = TimeSpan.FromHours(9), EndTime = TimeSpan.FromHours(9).Add(TimeSpan.FromMinutes(5)), Capacity = 5, BookedCount = 1 };
        db.TimeSlots.Add(slot);
        db.SaveChanges();

        var token = new Token { TokenNumber = "SR-TEST-000001", UserId = user.Id, RationShopId = shop.Id, TimeSlotId = slot.Id, Status = tokenStatus, CreatedAt = DateTime.UtcNow };
        db.Tokens.Add(token);
        db.SaveChanges();
        token.QRCodeValue = $"SRQR-{token.Id}-PLACEHOLDER"; // real signature computed by QrService in tests that need it
        db.TokenItems.Add(new TokenItem { TokenId = token.Id, RationType = RationType.Rice, Quantity = 5 });
        db.SaveChanges();

        return new BasicScenario(shop, scheme, user, beneficiary, family, slot, token);
    }
}
