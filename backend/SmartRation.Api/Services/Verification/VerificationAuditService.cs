using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Verification;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Services.Verification;

// Deliberately does not accept or store Aadhaar numbers, mobile numbers, or
// OTP codes — only the operational facts of a verification event.
public class VerificationAuditService(
    SmartRationDbContext db,
    IHttpContextAccessor httpContextAccessor,
    ICurrentUserService currentUser) : IVerificationAuditService
{
    public async Task LogAsync(
        VerificationAction action,
        string status,
        string verificationMethod,
        string? verificationReference = null,
        string? tokenNumber = null,
        int? beneficiaryId = null,
        int? shopId = null,
        string? reason = null)
    {
        int? operatorId = null;
        try
        {
            operatorId = currentUser.UserId;
        }
        catch
        {
            // No authenticated operator in context (shouldn't normally happen — every
            // verification endpoint requires auth — but audit logging must never throw).
        }

        var context = httpContextAccessor.HttpContext;

        db.VerificationAuditLogs.Add(new VerificationAuditLog
        {
            VerificationReference = verificationReference,
            TokenNumber = tokenNumber,
            BeneficiaryId = beneficiaryId,
            ShopId = shopId,
            Action = action,
            VerificationMethod = verificationMethod,
            Status = status,
            Reason = reason,
            OperatorId = operatorId,
            DeviceInfo = context?.Request.Headers.UserAgent.ToString(),
            IpAddress = context?.Connection.RemoteIpAddress?.ToString(),
            Timestamp = DateTime.UtcNow
        });

        await db.SaveChangesAsync();
    }

    public async Task<List<VerificationAuditLogDto>> QueryAsync(int? shopId, int? beneficiaryId, string? status, int take)
    {
        var query = db.VerificationAuditLogs.AsQueryable();
        if (shopId.HasValue) query = query.Where(l => l.ShopId == shopId);
        if (beneficiaryId.HasValue) query = query.Where(l => l.BeneficiaryId == beneficiaryId);
        if (!string.IsNullOrWhiteSpace(status)) query = query.Where(l => l.Status == status);

        var logs = await query
            .OrderByDescending(l => l.Timestamp)
            .Take(Math.Clamp(take, 1, 500))
            .ToListAsync();
        return logs.Select(l => l.ToDto()).ToList();
    }
}
