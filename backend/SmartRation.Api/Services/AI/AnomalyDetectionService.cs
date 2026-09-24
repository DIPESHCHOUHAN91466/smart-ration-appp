using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.AI;

public class AnomalyDetectionService(SmartRationDbContext db) : IAnomalyDetectionService
{
    public async Task<List<AIAlert>> ScanAndDetectAsync()
    {
        var windowStart = DateTime.UtcNow.AddHours(-24);
        var recentLogs = await db.VerificationAuditLogs
            .Where(l => l.Timestamp >= windowStart)
            .ToListAsync();

        var newAlerts = new List<AIAlert>();

        // 1. Repeated QR scans by the same beneficiary.
        foreach (var group in recentLogs.Where(l => l.Action == VerificationAction.QrScanned && l.BeneficiaryId != null).GroupBy(l => l.BeneficiaryId))
        {
            if (group.Count() > 3)
            {
                await UpsertAlertAsync(newAlerts, "RepeatedQrScan", AIAlertSeverity.Medium, beneficiaryId: group.Key,
                    description: $"{group.Count()} QR scans for this beneficiary in the last 24 hours.");
            }
        }

        // 2. Duplicate collection attempts on the same token.
        foreach (var group in recentLogs.Where(l => l.Action == VerificationAction.CollectionRejected && l.TokenNumber != null).GroupBy(l => l.TokenNumber))
        {
            if (group.Count() >= 2)
            {
                var shopId = group.First().ShopId;
                var beneficiaryId = group.First().BeneficiaryId;
                await UpsertAlertAsync(newAlerts, "DuplicateCollectionAttempt", AIAlertSeverity.High, shopId, beneficiaryId,
                    description: $"{group.Count()} rejected collection attempts on token {group.Key} in the last 24 hours.");
            }
        }

        // 3. Repeated failed/blocked verification for the same beneficiary.
        foreach (var group in recentLogs.Where(l => l.Action == VerificationAction.BeneficiaryVerified && l.Status == "BLOCKED" && l.BeneficiaryId != null).GroupBy(l => l.BeneficiaryId))
        {
            if (group.Count() >= 3)
            {
                await UpsertAlertAsync(newAlerts, "RepeatedFailedVerification", AIAlertSeverity.Medium, beneficiaryId: group.Key,
                    description: $"{group.Count()} blocked verification attempts for this beneficiary in the last 24 hours.");
            }
        }

        // 4. Unusual shop activity — today's scan volume vs trailing 7-day average.
        var sevenDaysAgo = DateTime.UtcNow.AddDays(-7);
        var weekLogs = await db.VerificationAuditLogs
            .Where(l => l.Timestamp >= sevenDaysAgo && l.Action == VerificationAction.QrScanned && l.ShopId != null)
            .Select(l => new { l.ShopId, l.Timestamp })
            .ToListAsync();

        foreach (var shopGroup in weekLogs.GroupBy(l => l.ShopId))
        {
            var todayCount = shopGroup.Count(l => l.Timestamp >= windowStart);
            var dailyAverage = shopGroup.Count(l => l.Timestamp < windowStart) / 6.0; // remaining 6 days' average

            if (dailyAverage > 0 && todayCount > dailyAverage * 2)
            {
                await UpsertAlertAsync(newAlerts, "UnusualShopActivity", AIAlertSeverity.Low, shopId: shopGroup.Key,
                    description: $"{todayCount} QR scans today vs a {dailyAverage:0.#}/day trailing average.");
            }
        }

        if (newAlerts.Count > 0)
        {
            await db.SaveChangesAsync();
        }

        return newAlerts;
    }

    public async Task<List<AIAlert>> GetRecentAlertsAsync(int take = 20)
    {
        return await db.AIAlerts
            .OrderByDescending(a => a.CreatedAt)
            .Take(take)
            .ToListAsync();
    }

    private async Task UpsertAlertAsync(List<AIAlert> newAlerts, string alertType, AIAlertSeverity severity, int? shopId = null, int? beneficiaryId = null, string description = "")
    {
        var windowStart = DateTime.UtcNow.AddHours(-24);
        var existing = await db.AIAlerts.AnyAsync(a =>
            a.AlertType == alertType &&
            a.ShopId == shopId &&
            a.BeneficiaryId == beneficiaryId &&
            a.Status == AIAlertStatus.Open &&
            a.CreatedAt >= windowStart);

        if (existing)
        {
            return;
        }

        var alert = new AIAlert
        {
            ShopId = shopId,
            BeneficiaryId = beneficiaryId,
            AlertType = alertType,
            Severity = severity,
            Description = description,
            Status = AIAlertStatus.Open,
            CreatedAt = DateTime.UtcNow
        };

        db.AIAlerts.Add(alert);
        newAlerts.Add(alert);

        if (shopId.HasValue)
        {
            var ownerUserId = await db.Users
                .Where(u => u.RationShopId == shopId.Value)
                .Select(u => (int?)u.Id)
                .FirstOrDefaultAsync();

            if (ownerUserId.HasValue)
            {
                db.Notifications.Add(new Notification
                {
                    UserId = ownerUserId.Value,
                    Type = NotificationType.AIAlert,
                    Title = $"AI Alert: {alertType}",
                    Message = description
                });
            }
        }
    }
}
