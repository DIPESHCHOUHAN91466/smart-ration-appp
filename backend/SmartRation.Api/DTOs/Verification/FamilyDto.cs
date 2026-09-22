namespace SmartRation.Api.DTOs.Verification;

public class FamilyMemberDto
{
    public int Id { get; set; }

    public string FullName { get; set; } = string.Empty;

    public int Age { get; set; }

    public string Relationship { get; set; } = string.Empty;

    public string Eligibility { get; set; } = string.Empty; // Eligible | NotEligible | Pending | VerificationRequired
}

public class FamilyDto
{
    public string FamilyCode { get; set; } = string.Empty;

    public string FamilyHeadName { get; set; } = string.Empty;

    public int FamilySize { get; set; }

    public int EligibleMemberCount { get; set; }

    public List<FamilyMemberDto> Members { get; set; } = [];
}
