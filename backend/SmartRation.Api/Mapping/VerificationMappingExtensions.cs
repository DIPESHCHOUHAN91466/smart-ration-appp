using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Models;

namespace SmartRation.Api.Mapping;

public static class VerificationMappingExtensions
{
    public static AadhaarVerificationDto ToDto(this AadhaarVerification a) => new()
    {
        Status = a.Status.ToString(),
        AadhaarMasked = a.AadhaarMasked,
        VerificationDate = a.VerificationDate?.ToString("yyyy-MM-dd"),
        VerificationSource = a.VerificationSource,
        VerificationMode = a.VerificationMode
    };

    public static PassbookVerificationDto ToDto(this PassbookVerification p) => new()
    {
        PassbookNumber = p.PassbookNumber,
        Status = p.Status,
        VerificationStatus = p.VerificationStatus.ToString(),
        LastUpdated = p.LastUpdated.ToString("yyyy-MM-dd"),
        VerificationSource = p.VerificationSource
    };

    public static MobileVerificationDto ToDto(this MobileVerification m) => new()
    {
        MobileMasked = m.MobileMasked,
        Status = m.Status.ToString(),
        VerifiedAt = m.VerifiedAt?.ToString("yyyy-MM-dd HH:mm")
    };

    public static BeneficiarySummaryDto ToDto(this Beneficiary b) => new()
    {
        Id = b.Id,
        BeneficiaryCode = b.BeneficiaryCode,
        FullName = b.User.FullName,
        MobileMasked = MaskingUtil.MaskMobile(b.User.MobileNumber),
        Address = b.Address,
        IsActive = b.IsActive,
        IsBlocked = b.IsBlocked
    };

    public static FamilyMemberDto ToDto(this FamilyMember m) => new()
    {
        Id = m.Id,
        FullName = m.FullName,
        Age = m.Age,
        Relationship = m.Relationship.ToString(),
        Eligibility = m.Eligibility.ToString()
    };

    public static FamilyDto ToDto(this Family f)
    {
        var head = f.Members.FirstOrDefault(m => m.Relationship == FamilyRelationship.Head);

        return new FamilyDto
        {
            FamilyCode = f.FamilyCode,
            FamilyHeadName = head?.FullName ?? string.Empty,
            FamilySize = f.Members.Count,
            EligibleMemberCount = f.Members.Count(m => m.Eligibility == EligibilityStatus.Eligible),
            Members = f.Members.Select(m => m.ToDto()).ToList()
        };
    }
}
