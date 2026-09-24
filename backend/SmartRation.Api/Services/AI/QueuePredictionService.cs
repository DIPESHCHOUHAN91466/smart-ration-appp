using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.AI;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.AI;

public class QueuePredictionService(SmartRationDbContext db) : IQueuePredictionService
{
    // Documented constant standing in for a measured average processing
    // time per collection — reasonable for a 5-minute-slot shop counter.
    private const int AverageMinutesPerCollection = 4;

    public async Task<List<QueuePredictionDto>> GetPredictionsAsync(int? shopId = null)
    {
        var today = DateTime.UtcNow.Date;

        var shopsQuery = db.RationShops.Where(s => s.IsActive).AsQueryable();
        if (shopId.HasValue)
        {
            shopsQuery = shopsQuery.Where(s => s.Id == shopId.Value);
        }
        var shops = await shopsQuery.ToListAsync();

        var results = new List<QueuePredictionDto>();

        foreach (var shop in shops)
        {
            var pending = await db.Tokens.CountAsync(t =>
                t.RationShopId == shop.Id &&
                t.TimeSlot.SlotDate.Date == today &&
                (t.Status == TokenStatus.Pending || t.Status == TokenStatus.Confirmed));

            var predictedWait = pending * AverageMinutesPerCollection;

            results.Add(new QueuePredictionDto
            {
                ShopId = shop.Id,
                ShopName = shop.ShopName,
                PendingInQueue = pending,
                PredictedWaitMinutes = predictedWait,
                Explanation = $"{pending} beneficiaries pending today × ~{AverageMinutesPerCollection} min average verification/collection time."
            });
        }

        return results;
    }
}
