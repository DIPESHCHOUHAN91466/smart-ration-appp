namespace SmartRation.Api.Models;

public class Family
{
    public int Id { get; set; }

    public string FamilyCode { get; set; } = string.Empty; // FAM-DEMO-0001

    public int RationShopId { get; set; }

    public RationShop RationShop { get; set; } = null!;

    public int RationSchemeId { get; set; }

    public RationScheme RationScheme { get; set; } = null!;

    public string DataSource { get; set; } = "SYNTHETIC_DEMO";

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<FamilyMember> Members { get; set; } = new List<FamilyMember>();

    public ICollection<Beneficiary> Beneficiaries { get; set; } = new List<Beneficiary>();
}
