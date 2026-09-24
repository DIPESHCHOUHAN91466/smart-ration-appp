namespace SmartRation.Api.DTOs.Admin;

public class PagedResultDto<T>
{
    public List<T> Items { get; set; } = [];

    public int TotalCount { get; set; }

    public int Page { get; set; }

    public int PageSize { get; set; }
}

public class SyntheticBeneficiaryRowDto
{
    public int Id { get; set; }

    public string BeneficiaryCode { get; set; } = string.Empty;

    public string FullName { get; set; } = string.Empty;

    public string Gender { get; set; } = string.Empty;

    public string Village { get; set; } = string.Empty;

    public string District { get; set; } = string.Empty;

    public string State { get; set; } = string.Empty;

    public string SchemeCode { get; set; } = string.Empty;

    public string ShopName { get; set; } = string.Empty;

    public int FamilySize { get; set; }

    public string AadhaarStatus { get; set; } = string.Empty;

    public string PassbookStatus { get; set; } = string.Empty;

    public bool IsActive { get; set; }

    public bool IsBlocked { get; set; }
}
