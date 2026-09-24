using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.AI;

public class DemandForecastService(SmartRationDbContext db) : IDemandForecastService
{
    public async Task<List<DemandForecastDto>> GetForecastAsync(int? shopId = null)
    {
        var now = DateTime.UtcNow;
        var last30Start = now.AddDays(-30);
        var prior30Start = now.AddDays(-60);

        var query = db.RationCollectionItems
            .Where(ci => ci.RationCollection.CollectedAt >= prior30Start)
            .AsQueryable();

        if (shopId.HasValue)
        {
            query = query.Where(ci => ci.RationCollection.RationShopId == shopId.Value);
        }

        // Materialize (SQLite can't Sum a decimal column server-side) then aggregate client-side.
        var rows = await query
            .Select(ci => new { ci.RationType, ci.Quantity, ci.RationCollection.CollectedAt })
            .ToListAsync();

        var results = new List<DemandForecastDto>();

        foreach (var rationType in Enum.GetValues<RationType>())
        {
            var last30 = rows.Where(r => r.RationType == rationType && r.CollectedAt >= last30Start).Sum(r => r.Quantity);
            var prior30 = rows.Where(r => r.RationType == rationType && r.CollectedAt >= prior30Start && r.CollectedAt < last30Start).Sum(r => r.Quantity);

            var growthPercent = prior30 > 0 ? (double)((last30 - prior30) / prior30) * 100.0 : 0;
            var predicted = last30 * (1 + (decimal)growthPercent / 100m);

            results.Add(new DemandForecastDto
            {
                RationType = rationType.ToString(),
                Last30DaysKg = last30,
                Previous30DaysKg = prior30,
                GrowthPercent = Math.Round(growthPercent, 1),
                PredictedNext30DaysKg = Math.Round(Math.Max(0, predicted), 1)
            });
        }

        return results;
    }
}
