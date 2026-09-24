using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.AI;

public class BeneficiaryInsightService(SmartRationDbContext db) : IBeneficiaryInsightService
{
    public async Task<BeneficiaryRiskInsightDto> GetBeneficiaryInsightAsync(int beneficiaryId)
    {
        var windowStart = DateTime.UtcNow.AddHours(-24);

        var recentLogs = await db.VerificationAuditLogs
            .Where(l => l.BeneficiaryId == beneficiaryId && l.Timestamp >= windowStart)
            .ToListAsync();

        var qrScanCount = recentLogs.Count(l => l.Action == VerificationAction.QrScanned);
        var blockedCount = recentLogs.Count(l => l.Action == VerificationAction.BeneficiaryVerified && l.Status == "BLOCKED");

        var openAlerts = await db.AIAlerts.CountAsync(a => a.BeneficiaryId == beneficiaryId && a.Status == AIAlertStatus.Open);

        var reasons = new List<string>();
        if (qrScanCount > 3) reasons.Add($"{qrScanCount} repeated QR scan attempts in the last 24 hours");
        if (blockedCount > 0) reasons.Add($"{blockedCount} blocked verification attempt(s) recently");
        if (openAlerts > 0) reasons.Add($"{openAlerts} open anomaly alert(s) on record");

        string riskLevel;
        string explanation;

        if (openAlerts >= 2 || blockedCount >= 3)
        {
            riskLevel = "High";
            explanation = "Multiple unresolved anomaly signals for this beneficiary — review verification history before confirming collection.";
        }
        else if (reasons.Count > 0)
        {
            riskLevel = "Medium";
            explanation = "Some recent activity is outside the beneficiary's usual pattern — a quick review is recommended.";
        }
        else
        {
            riskLevel = "Low";
            explanation = "Collection pattern is consistent with the beneficiary's entitlement schedule.";
            reasons.Add("No anomalies detected in the last 24 hours");
        }

        var riskEnum = riskLevel switch
        {
            "High" => AIRiskLevel.High,
            "Medium" => AIRiskLevel.Medium,
            _ => AIRiskLevel.Low
        };

        db.AIInsights.Add(new AIInsight
        {
            EntityType = "Beneficiary",
            EntityId = beneficiaryId,
            InsightType = "BeneficiaryRisk",
            RiskLevel = riskEnum,
            Score = qrScanCount + blockedCount + openAlerts,
            Explanation = explanation,
            Recommendation = riskLevel == "Low" ? "No action required." : "Review verification history before confirming collection."
        });
        await db.SaveChangesAsync();

        return new BeneficiaryRiskInsightDto
        {
            RiskLevel = riskLevel,
            Reasons = reasons,
            Explanation = explanation
        };
    }
}
