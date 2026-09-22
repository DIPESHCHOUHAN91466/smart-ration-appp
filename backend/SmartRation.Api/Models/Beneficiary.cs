namespace SmartRation.Api.Models;

// A beneficiary profile extends a RuralUser account with the verification
// and entitlement identity the ration-shop workflow needs. One User has at
// most one Beneficiary profile, auto-provisioned at registration.
public class Beneficiary
{
    public int Id { get; set; }

    public string BeneficiaryCode { get; set; } = string.Empty; // BEN-DEMO-0001

    // Synthetic demo address (village-level only — never a real residential address).
    public string Address { get; set; } = string.Empty;

    public int UserId { get; set; }

    public User User { get; set; } = null!;

    public int FamilyId { get; set; }

    public Family Family { get; set; } = null!;

    public bool IsActive { get; set; } = true;

    public bool IsBlocked { get; set; } = false;

    // Always "SYNTHETIC_DEMO" until real registries are integrated.
    public string DataSource { get; set; } = "SYNTHETIC_DEMO";

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public AadhaarVerification? AadhaarVerification { get; set; }

    public PassbookVerification? PassbookVerification { get; set; }

    public MobileVerification? MobileVerification { get; set; }
}
