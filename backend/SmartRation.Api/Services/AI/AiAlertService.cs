using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.AI;

public interface IAiAlertService
{
    // Pulls alert candidates from the Python service and upserts them.
    Task<AiAlertSyncResultDto> SyncFromPythonAsync(bool force, CancellationToken ct = default);

    Task<List<AiAlertDto>> ListAsync(AiAlertQuery query);

    Task<AiAlertDto> GetAsync(int id);

    Task<AiAlertDto> ResolveAsync(int id, ResolveAiAlertRequestDto request);
}

public record AiAlertQuery(string? Status, int? ShopId, string? Source, int Limit);

// Persists Python AI findings into the existing AIAlerts table.
//  * Deduplication: while an alert with the same DedupKey is Open/UnderReview,
//    re-detection only refreshes it (LastSeenAt, score, text) — refreshing the
//    dashboard any number of times never adds rows.
//  * Throttled: automatic syncs run at most once per SyncInterval.
//  * Scoped: shop owners only ever see their own shop's alerts.
//  * Alerts are review prompts, never proof of fraud; nothing here acts on them.
public class AiAlertService(
    SmartRationDbContext db,
    IPythonAiClient pythonAi,
    ICurrentUserService currentUser,
    IAuditLogService auditLog,
    ILogger<AiAlertService> logger) : IAiAlertService
{
    public const string PythonSource = "PYTHON_AI";
    private static readonly TimeSpan SyncInterval = TimeSpan.FromMinutes(5);
    private static readonly SemaphoreSlim SyncLock = new(1, 1);
    private static DateTime? _lastSyncUtc;

    private static readonly AIAlertStatus[] ActiveStatuses = [AIAlertStatus.Open, AIAlertStatus.UnderReview];

    public async Task<AiAlertSyncResultDto> SyncFromPythonAsync(bool force, CancellationToken ct = default)
    {
        if (!force && _lastSyncUtc is { } last && DateTime.UtcNow - last < SyncInterval)
        {
            return new AiAlertSyncResultDto { Skipped = true, LastAnalysisAt = last, Message = "Recently analysed." };
        }

        // Serialize syncs: two concurrent refreshes must not both insert the same alert.
        await SyncLock.WaitAsync(ct);
        try
        {
            var result = await pythonAi.GetAsync("/v1/alerts", new Dictionary<string, string?> { ["lang"] = "en" }, ct);
            if (!result.Available || result.Data is not { } data || !data.TryGetProperty("items", out var items) || items.ValueKind != JsonValueKind.Array)
            {
                return new AiAlertSyncResultDto
                {
                    Available = false,
                    LastAnalysisAt = _lastSyncUtc,
                    ErrorCode = result.ErrorCode ?? "AI_MALFORMED_RESPONSE",
                    Message = result.Message ?? "The AI service returned no alert data."
                };
            }

            var now = DateTime.UtcNow;
            var outcome = new AiAlertSyncResultDto { Available = true };

            foreach (var item in items.EnumerateArray())
            {
                var candidate = Parse(item);
                if (candidate is null)
                {
                    outcome.Rejected++;
                    continue;
                }

                var existing = await db.AIAlerts.FirstOrDefaultAsync(a =>
                    a.DedupKey == candidate.DedupKey && ActiveStatuses.Contains(a.Status), ct);

                if (existing is not null)
                {
                    existing.LastSeenAt = now;
                    existing.Score = candidate.Score;
                    existing.Severity = (AIAlertSeverity)Math.Max((int)existing.Severity, (int)candidate.Severity);
                    existing.Description = candidate.Description;
                    existing.MetadataJson = candidate.MetadataJson;
                    outcome.Updated++;
                    continue;
                }

                candidate.DetectedAt = now;
                candidate.LastSeenAt = now;
                candidate.CreatedAt = now;
                db.AIAlerts.Add(candidate);
                outcome.Created++;
            }

            await db.SaveChangesAsync(ct);
            _lastSyncUtc = now;
            outcome.LastAnalysisAt = now;

            if (outcome.Created > 0)
            {
                await auditLog.LogAsync(currentUser.UserId, "AI_ALERTS_CREATED", nameof(AIAlert),
                    details: $"created={outcome.Created} updated={outcome.Updated} source={PythonSource}");
            }
            logger.LogInformation("AI alert sync: {Created} created, {Updated} refreshed, {Rejected} rejected", outcome.Created, outcome.Updated, outcome.Rejected);
            return outcome;
        }
        finally
        {
            SyncLock.Release();
        }
    }

    public async Task<List<AiAlertDto>> ListAsync(AiAlertQuery query)
    {
        var q = Scoped(db.AIAlerts.AsNoTracking());

        if (query.ShopId is { } shopId)
        {
            q = q.Where(a => a.ShopId == shopId);
        }
        if (!string.IsNullOrWhiteSpace(query.Source))
        {
            q = q.Where(a => a.Source == query.Source);
        }
        q = query.Status?.ToLowerInvariant() switch
        {
            null or "" or "all" => q,
            "active" => q.Where(a => ActiveStatuses.Contains(a.Status)),
            var s when Enum.TryParse<AIAlertStatus>(s, true, out var status) => q.Where(a => a.Status == status),
            _ => throw new BadRequestException("Unknown alert status filter.") { ErrorCode = "INVALID_STATUS" }
        };

        var rows = await q
            .OrderByDescending(a => a.Severity)
            .ThenByDescending(a => a.LastSeenAt ?? a.CreatedAt)
            .Take(Math.Clamp(query.Limit, 1, 200))
            .ToListAsync();
        return await WithShopNamesAsync(rows);
    }

    public async Task<AiAlertDto> GetAsync(int id)
    {
        var alert = await Scoped(db.AIAlerts.AsNoTracking()).FirstOrDefaultAsync(a => a.Id == id)
            ?? throw new NotFoundException("Alert not found.");
        return (await WithShopNamesAsync([alert]))[0];
    }

    public async Task<AiAlertDto> ResolveAsync(int id, ResolveAiAlertRequestDto request)
    {
        if (currentUser.Role is not (UserRole.GovernmentOfficial or UserRole.Admin))
        {
            throw new ForbiddenException("Only government officials can resolve alerts.");
        }
        if (!Enum.TryParse<AIAlertStatus>(request.Status, true, out var status) || status == AIAlertStatus.Open)
        {
            throw new BadRequestException("Status must be UnderReview, Resolved or Dismissed.") { ErrorCode = "INVALID_STATUS" };
        }

        var alert = await db.AIAlerts.FirstOrDefaultAsync(a => a.Id == id)
            ?? throw new NotFoundException("Alert not found.");

        alert.Status = status;
        alert.ResolutionNote = request.Note?.Trim();
        if (status is AIAlertStatus.Resolved or AIAlertStatus.Dismissed)
        {
            alert.ResolvedAt = DateTime.UtcNow;
            alert.ResolvedByUserId = currentUser.UserId;
        }
        await db.SaveChangesAsync();

        await auditLog.LogAsync(currentUser.UserId, "AI_ALERT_" + status.ToString().ToUpperInvariant(), nameof(AIAlert), alert.Id.ToString(), $"{alert.AlertType} {alert.DedupKey}");
        return (await WithShopNamesAsync([alert]))[0];
    }

    // Shop owners: own shop only (and never shop-less/system-wide alerts).
    private IQueryable<AIAlert> Scoped(IQueryable<AIAlert> q) => currentUser.Role switch
    {
        UserRole.GovernmentOfficial or UserRole.Admin => q,
        UserRole.ShopOwner => q.Where(a => a.ShopId != null && a.ShopId == currentUser.RationShopId),
        _ => q.Where(_ => false)
    };

    private async Task<List<AiAlertDto>> WithShopNamesAsync(List<AIAlert> alerts)
    {
        var shopIds = alerts.Where(a => a.ShopId.HasValue).Select(a => a.ShopId!.Value).Distinct().ToList();
        var names = await db.RationShops.Where(s => shopIds.Contains(s.Id)).ToDictionaryAsync(s => s.Id, s => s.ShopName);
        return alerts.Select(a => AiAlertDto.From(a, a.ShopId is { } sid ? names.GetValueOrDefault(sid) : null)).ToList();
    }

    // Validates one candidate from the AI service; malformed entries are skipped, not trusted.
    private static AIAlert? Parse(JsonElement item)
    {
        try
        {
            var dedupKey = item.GetProperty("dedup_key").GetString();
            var type = item.GetProperty("alert_type").GetString();
            var severityText = item.GetProperty("severity").GetString();
            if (string.IsNullOrWhiteSpace(dedupKey) || dedupKey.Length > 128 || string.IsNullOrWhiteSpace(type) || type.Length > 64
                || !Enum.TryParse<AIAlertSeverity>(severityText, true, out var severity))
            {
                return null;
            }

            int? shopId = item.TryGetProperty("shop_id", out var s) && s.ValueKind == JsonValueKind.Number ? s.GetInt32() : null;
            RationType? rationType = item.TryGetProperty("ration_type", out var r) && r.ValueKind == JsonValueKind.Number
                && Enum.IsDefined(typeof(RationType), r.GetInt32()) ? (RationType)r.GetInt32() : null;
            double? score = item.TryGetProperty("score", out var sc) && sc.ValueKind == JsonValueKind.Number ? Math.Clamp(sc.GetDouble(), 0, 100) : null;

            return new AIAlert
            {
                Source = PythonSource,
                DedupKey = dedupKey,
                AlertType = type,
                Severity = severity,
                ShopId = shopId,
                RationType = rationType,
                Score = score,
                Title = Truncate(item.TryGetProperty("title", out var t) ? t.GetString() : null, 200),
                Description = Truncate(item.TryGetProperty("description", out var d) ? d.GetString() : null, 2000) ?? string.Empty,
                RecommendedAction = Truncate(item.TryGetProperty("recommended_action", out var a) ? a.GetString() : null, 500),
                MetadataJson = item.TryGetProperty("metadata", out var m) && m.ValueKind == JsonValueKind.Object ? Truncate(m.GetRawText(), 4000) : null,
                Status = AIAlertStatus.Open
            };
        }
        catch (Exception ex) when (ex is KeyNotFoundException or InvalidOperationException or FormatException)
        {
            return null;
        }
    }

    private static string? Truncate(string? value, int max) => value is null ? null : value.Length <= max ? value : value[..max];
}
