namespace SmartRation.Api.Models;

public enum FamilyRelationship
{
    Head = 1,
    Spouse = 2,
    Son = 3,
    Daughter = 4,
    Parent = 5,
    Other = 6
}

public enum EligibilityStatus
{
    Eligible = 1,
    NotEligible = 2,
    Pending = 3,
    VerificationRequired = 4
}

public class FamilyMember
{
    public int Id { get; set; }

    public int FamilyId { get; set; }

    public Family Family { get; set; } = null!;

    public string FullName { get; set; } = string.Empty;

    public int Age { get; set; }

    public FamilyRelationship Relationship { get; set; }

    public EligibilityStatus Eligibility { get; set; } = EligibilityStatus.Eligible;

    public string DataSource { get; set; } = "SYNTHETIC_DEMO";
}
