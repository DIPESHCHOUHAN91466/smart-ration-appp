namespace SmartRation.Api.Models;

public enum Gender
{
    Male = 1,
    Female = 2,
    Other = 3
}

// A beneficiary profile extends a RuralUser account with the verification
// and entitlement identity the ration-shop workflow needs. One User has at
// most one Beneficiary profile, auto-provisioned at registration.
public class Beneficiary
{
    public int Id { get; set; }

    public string BeneficiaryCode { get; set; } = string.Empty; // BEN-DEMO-0001

    // Synthetic demo address (village-level only — never a real residential address).
    public string Address { get; set; } = string.Empty;

    public Gender Gender { get; set; } = Gender.Other;

    // Synthetic demo date of birth — never a real beneficiary's actual DOB.
    public DateTime DateOfBirth { get; set; }

    public string Village { get; set; } = string.Empty;

    public string District { get; set; } = string.Empty;

    public string State { get; set; } = string.Empty;

    public string Pincode { get; set; } = string.Empty;

    // Null by default — the UI falls back to an initials avatar (same pattern
    // used everywhere else in this app) rather than a fake external photo URL.
    public string? ProfilePhotoUrl { get; set; }

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
