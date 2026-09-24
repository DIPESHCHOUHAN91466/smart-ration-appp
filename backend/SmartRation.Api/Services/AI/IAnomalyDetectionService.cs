using SmartRation.Api.Models;

namespace SmartRation.Api.Services.AI;

public interface IAnomalyDetectionService
{
    // Scans recent VerificationAuditLog activity for the rule-based anomaly
    // patterns and upserts AIAlert rows (idempotent — won't duplicate an
    // already-open alert for the same subject within the detection window).
    Task<List<AIAlert>> ScanAndDetectAsync();

    Task<List<AIAlert>> GetRecentAlertsAsync(int take = 20);
}
