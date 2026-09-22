namespace SmartRation.Api.Models;

// The actual issuance transaction recorded when a shop confirms collection
// through the beneficiary verification flow. Distinct from (and linked to)
// the existing Token, which already tracks Status/CollectedAt for the
// simpler quick-complete path — this is the richer, entitlement-aware
// receipt record.
public class RationCollection
{
    public int Id { get; set; }

    public string CollectionCode { get; set; } = string.Empty; // COL-DEMO-000001

    public int TokenId { get; set; }

    public Token Token { get; set; } = null!;

    public int BeneficiaryId { get; set; }

    public Beneficiary Beneficiary { get; set; } = null!;

    public int RationShopId { get; set; }

    public RationShop RationShop { get; set; } = null!;

    public int OperatorUserId { get; set; }

    // QR or OTP — which verification path led to this collection.
    public string VerificationMethod { get; set; } = string.Empty;

    public DateTime CollectedAt { get; set; } = DateTime.UtcNow;

    public ICollection<RationCollectionItem> Items { get; set; } = new List<RationCollectionItem>();
}

public class RationCollectionItem
{
    public int Id { get; set; }

    public int RationCollectionId { get; set; }

    public RationCollection RationCollection { get; set; } = null!;

    public RationType RationType { get; set; }

    public decimal Quantity { get; set; }
}
