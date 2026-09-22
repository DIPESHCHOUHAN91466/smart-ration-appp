namespace SmartRation.Api.DTOs.Verification;

public class BeneficiarySummaryDto
{
    public int Id { get; set; }

    public string BeneficiaryCode { get; set; } = string.Empty;

    public string FullName { get; set; } = string.Empty;

    public string MobileMasked { get; set; } = string.Empty;

    public string Address { get; set; } = string.Empty;

    public bool IsActive { get; set; }

    public bool IsBlocked { get; set; }
}
