using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Government;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services;

public class GovernmentService(SmartRationDbContext db) : IGovernmentService
{
    public async Task<GovernmentDashboardDto> GetDashboardAsync()
    {
        var today = DateTime.UtcNow.Date;

        var totalBeneficiaries = await db.Users.CountAsync(u => u.Role == UserRole.RuralUser && u.IsActive);
        var totalShops = await db.RationShops.CountAsync(s => s.IsActive);

        var todaysTokens = await db.Tokens
            .Where(t => t.TimeSlot.SlotDate.Date == today)
            .Select(t => t.Status)
            .ToListAsync();

        // SQLite can't translate Sum over a decimal column server-side, so pull the quantities and sum client-side.
        var distributedTodayKg = (await db.TokenItems
            .Where(ti => ti.Token.Status == TokenStatus.Completed && ti.Token.CollectedAt != null && ti.Token.CollectedAt.Value.Date == today)
            .Select(ti => ti.Quantity)
            .ToListAsync())
            .Sum();

        var lowStockAlerts = await db.Inventory.CountAsync(i => i.AvailableQuantity <= i.MinimumStockLevel);

        return new GovernmentDashboardDto
        {
            TotalBeneficiaries = totalBeneficiaries,
            TotalShops = totalShops,
            TodayBookings = todaysTokens.Count,
            TodayCollections = todaysTokens.Count(s => s == TokenStatus.Completed),
            PendingCollections = todaysTokens.Count(s => s is TokenStatus.Pending or TokenStatus.Confirmed),
            RationDistributedTodayKg = distributedTodayKg,
            LowStockAlerts = lowStockAlerts
        };
    }

    public async Task<StatisticsDto> GetStatisticsAsync(DateTime? fromDate, DateTime? toDate)
    {
        var (from, to) = NormalizeRange(fromDate, toDate);

        var tokensInRange = await db.Tokens
            .Where(t => t.CreatedAt.Date >= from && t.CreatedAt.Date <= to)
            .Include(t => t.RationShop)
            .ToListAsync();

        var completed = tokensInRange.Count(t => t.Status == TokenStatus.Completed);
        var cancelled = tokensInRange.Count(t => t.Status == TokenStatus.Cancelled);
        var efficiency = tokensInRange.Count == 0 ? 0 : Math.Round(completed * 100.0 / tokensInRange.Count, 1);

        var shopPerformance = tokensInRange
            .GroupBy(t => new { t.RationShopId, t.RationShop.ShopName })
            .Select(g => new ShopPerformanceDto
            {
                ShopId = g.Key.RationShopId,
                ShopName = g.Key.ShopName,
                TotalTokens = g.Count(),
                CompletedTokens = g.Count(t => t.Status == TokenStatus.Completed),
                EfficiencyPercent = g.Count() == 0 ? 0 : Math.Round(g.Count(t => t.Status == TokenStatus.Completed) * 100.0 / g.Count(), 1)
            })
            .OrderByDescending(s => s.EfficiencyPercent)
            .ToList();

        return new StatisticsDto
        {
            FromDate = from,
            ToDate = to,
            TokensGenerated = tokensInRange.Count,
            CollectionsCompleted = completed,
            CollectionsCancelled = cancelled,
            CollectionEfficiencyPercent = efficiency,
            ShopPerformance = shopPerformance
        };
    }

    public async Task<IReadOnlyList<ReportSummaryDto>> GetReportsAsync(DateTime? fromDate, DateTime? toDate)
    {
        var (from, to) = NormalizeRange(fromDate, toDate);

        var tokensInRange = await db.Tokens
            .Where(t => t.CreatedAt.Date >= from && t.CreatedAt.Date <= to)
            .ToListAsync();

        var qrVerifications = await db.AuditLogs
            .CountAsync(a => a.Action == "COLLECTION_COMPLETED" && a.CreatedAt.Date >= from && a.CreatedAt.Date <= to);

        return
        [
            new ReportSummaryDto { ReportName = "Daily Collection Report", Description = "Ration collections completed in range", RecordCount = tokensInRange.Count(t => t.Status == TokenStatus.Completed) },
            new ReportSummaryDto { ReportName = "Token Generation Report", Description = "Ration tokens generated in range", RecordCount = tokensInRange.Count },
            new ReportSummaryDto { ReportName = "QR Verification Report", Description = "Successful QR verifications resulting in collection", RecordCount = qrVerifications },
            new ReportSummaryDto { ReportName = "Cancelled Bookings Report", Description = "Bookings cancelled in range", RecordCount = tokensInRange.Count(t => t.Status == TokenStatus.Cancelled) }
        ];
    }

    private static (DateTime From, DateTime To) NormalizeRange(DateTime? fromDate, DateTime? toDate)
    {
        var to = (toDate ?? DateTime.UtcNow).Date;
        var from = (fromDate ?? to.AddDays(-29)).Date;
        return from <= to ? (from, to) : (to, from);
    }
}
