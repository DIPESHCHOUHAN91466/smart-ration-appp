namespace SmartRation.Api.Models;

public class RationScheme
{
    public int Id { get; set; }

    public string SchemeCode { get; set; } = string.Empty; // DEMO-NFSA

    public string Name { get; set; } = string.Empty;

    public string Description { get; set; } = string.Empty;

    public bool IsActive { get; set; } = true;

    public ICollection<SchemeEntitlementItem> EntitlementItems { get; set; } = new List<SchemeEntitlementItem>();

    public ICollection<Family> Families { get; set; } = new List<Family>();
}

// The per-item monthly rate a scheme grants per eligible family member —
// the entitlement engine reads this instead of any hard-coded quantity.
public class SchemeEntitlementItem
{
    public int Id { get; set; }

    public int RationSchemeId { get; set; }

    public RationScheme RationScheme { get; set; } = null!;

    public RationType RationType { get; set; }

    public decimal QuotaPerEligibleMemberPerMonth { get; set; }
}
