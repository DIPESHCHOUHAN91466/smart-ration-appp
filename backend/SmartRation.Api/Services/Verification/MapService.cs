using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Common;
using SmartRation.Api.Data;
using SmartRation.Api.DTOs.Map;
using SmartRation.Api.Mapping;
using SmartRation.Api.Models;

namespace SmartRation.Api.Services.Verification;

// DEMO MAP DATA — shop coordinates are the same synthetic demo coordinates
// used everywhere else in this system; heatmap weights are computed from
// real (but synthetic-seeded) database counts, never from individual
// beneficiary locations, which this system does not collect.
public class MapService(SmartRationDbContext db) : IMapService
{
    public async Task<List<ShopMapMarkerDto>> GetShopMarkersAsync(
        string? state, string? district, string? taluka, string? village, string? schemeCode, string? inventoryStatus)
    {
        var shopsQuery = db.RationShops.Where(s => s.IsActive).AsQueryable();

        if (!string.IsNullOrWhiteSpace(state)) shopsQuery = shopsQuery.Where(s => s.State == state);
        if (!string.IsNullOrWhiteSpace(district)) shopsQuery = shopsQuery.Where(s => s.District == district);
        if (!string.IsNullOrWhiteSpace(taluka)) shopsQuery = shopsQuery.Where(s => s.Taluka == taluka);
        if (!string.IsNullOrWhiteSpace(village)) shopsQuery = shopsQuery.Where(s => s.Village == village);

        var shops = await shopsQuery.ToListAsync();

        if (!string.IsNullOrWhiteSpace(schemeCode))
        {
            var shopIdsWithScheme = await db.Families
                .Where(f => f.RationScheme.SchemeCode == schemeCode)
                .Select(f => f.RationShopId)
                .Distinct()
                .ToListAsync();
            shops = shops.Where(s => shopIdsWithScheme.Contains(s.Id)).ToList();
        }

        var markers = new List<ShopMapMarkerDto>();
        foreach (var shop in shops)
        {
            var marker = await BuildMarkerAsync(shop);
            markers.Add(marker);
        }

        if (!string.IsNullOrWhiteSpace(inventoryStatus))
        {
            markers = markers.Where(m => string.Equals(m.InventoryStatus, inventoryStatus, StringComparison.OrdinalIgnoreCase)).ToList();
        }

        return markers;
    }

    public async Task<ShopMapDetailDto> GetShopDetailAsync(int shopId)
    {
        var shop = await db.RationShops.FirstOrDefaultAsync(s => s.Id == shopId)
            ?? throw new NotFoundException("Ration shop not found.");

        var operatorName = await db.Users
            .Where(u => u.RationShopId == shopId && u.Role == UserRole.ShopOwner)
            .Select(u => u.FullName)
            .FirstOrDefaultAsync();

        var inventory = await db.Inventory.Where(i => i.RationShopId == shopId).ToListAsync();
        var stats = await ComputeShopStatsAsync(shopId);

        return new ShopMapDetailDto
        {
            Id = shop.Id,
            ShopName = shop.ShopName,
            ShopCode = shop.ShopCode,
            OperatorName = operatorName,
            Village = shop.Village ?? shop.Address,
            District = shop.District,
            State = shop.State,
            Latitude = shop.Latitude,
            Longitude = shop.Longitude,
            Inventory = inventory.Select(i => i.ToDto()).ToList(),
            TodayBookings = stats.TodayBookings,
            CompletedCollections = stats.CompletedCollections,
            PendingCollections = stats.PendingCollections,
            EligibleBeneficiaries = stats.EligibleBeneficiaries,
            VerificationIssues = stats.VerificationIssues
        };
    }

    public async Task<MapAnalyticsDto> GetAnalyticsAsync()
    {
        var shops = await db.RationShops.ToListAsync();
        var today = DateTime.UtcNow.Date;

        var beneficiaryDensity = new List<DTOs.Map.HeatmapPointDto>();
        var demand = new List<DTOs.Map.HeatmapPointDto>();
        var collectionActivity = new List<DTOs.Map.HeatmapPointDto>();
        var inventoryShortage = new List<DTOs.Map.HeatmapPointDto>();

        var lowCount = 0;
        var criticalCount = 0;
        var totalTodayCollections = 0;
        var totalPending = 0;

        foreach (var shop in shops)
        {
            var stats = await ComputeShopStatsAsync(shop.Id);
            var (status, shortfall) = await ComputeInventoryStatusAsync(shop.Id);

            if (status == "Low") lowCount++;
            if (status == "Critical") criticalCount++;

            totalTodayCollections += stats.CompletedCollections;
            totalPending += stats.PendingCollections;

            if (stats.EligibleBeneficiaries > 0)
            {
                beneficiaryDensity.Add(new DTOs.Map.HeatmapPointDto { Lat = shop.Latitude, Lng = shop.Longitude, Intensity = stats.EligibleBeneficiaries });
            }

            if (stats.TodayBookings > 0)
            {
                demand.Add(new DTOs.Map.HeatmapPointDto { Lat = shop.Latitude, Lng = shop.Longitude, Intensity = stats.TodayBookings });
            }

            if (stats.CompletedCollections > 0)
            {
                collectionActivity.Add(new DTOs.Map.HeatmapPointDto { Lat = shop.Latitude, Lng = shop.Longitude, Intensity = stats.CompletedCollections });
            }

            if (shortfall > 0)
            {
                inventoryShortage.Add(new DTOs.Map.HeatmapPointDto { Lat = shop.Latitude, Lng = shop.Longitude, Intensity = (double)shortfall });
            }
        }

        var totalBeneficiaries = await db.Beneficiaries.CountAsync(b => b.IsActive && !b.IsBlocked);
        var eligibleBeneficiaries = await db.FamilyMembers.CountAsync(m => m.Eligibility == EligibilityStatus.Eligible);

        return new MapAnalyticsDto
        {
            TotalShops = shops.Count,
            ActiveShops = shops.Count(s => s.IsActive),
            LowInventoryShops = lowCount,
            CriticalInventoryShops = criticalCount,
            TotalBeneficiaries = totalBeneficiaries,
            EligibleBeneficiaries = eligibleBeneficiaries,
            TodayCollections = totalTodayCollections,
            PendingCollections = totalPending,
            BeneficiaryDensityHeatmap = beneficiaryDensity,
            DemandHeatmap = demand,
            CollectionActivityHeatmap = collectionActivity,
            InventoryShortageHeatmap = inventoryShortage,
            IsSyntheticData = true
        };
    }

    private async Task<ShopMapMarkerDto> BuildMarkerAsync(RationShop shop)
    {
        var stats = await ComputeShopStatsAsync(shop.Id);
        var (status, _) = await ComputeInventoryStatusAsync(shop.Id);

        return new ShopMapMarkerDto
        {
            Id = shop.Id,
            ShopName = shop.ShopName,
            ShopCode = shop.ShopCode,
            Latitude = shop.Latitude,
            Longitude = shop.Longitude,
            State = shop.State,
            District = shop.District,
            Taluka = shop.Taluka,
            Village = shop.Village,
            InventoryStatus = status,
            TodayBookings = stats.TodayBookings,
            CompletedCollections = stats.CompletedCollections,
            PendingCollections = stats.PendingCollections,
            EligibleBeneficiaries = stats.EligibleBeneficiaries,
            VerificationIssues = stats.VerificationIssues
        };
    }

    private async Task<(int TodayBookings, int CompletedCollections, int PendingCollections, int EligibleBeneficiaries, int VerificationIssues)> ComputeShopStatsAsync(int shopId)
    {
        var today = DateTime.UtcNow.Date;

        var todaysStatuses = await db.Tokens
            .Where(t => t.RationShopId == shopId && t.TimeSlot.SlotDate.Date == today)
            .Select(t => t.Status)
            .ToListAsync();

        var eligibleBeneficiaries = await db.Beneficiaries
            .Where(b => b.Family.RationShopId == shopId && b.IsActive && !b.IsBlocked)
            .CountAsync();

        var beneficiaryIds = await db.Beneficiaries
            .Where(b => b.Family.RationShopId == shopId)
            .Select(b => b.Id)
            .ToListAsync();

        var verificationIssues = 0;
        if (beneficiaryIds.Count > 0)
        {
            verificationIssues = await db.AadhaarVerifications
                .Where(a => beneficiaryIds.Contains(a.BeneficiaryId) && a.Status != AadhaarVerificationStatus.Verified)
                .CountAsync();
        }

        return (
            TodayBookings: todaysStatuses.Count,
            CompletedCollections: todaysStatuses.Count(s => s == TokenStatus.Completed),
            PendingCollections: todaysStatuses.Count(s => s is TokenStatus.Pending or TokenStatus.Confirmed),
            EligibleBeneficiaries: eligibleBeneficiaries,
            VerificationIssues: verificationIssues);
    }

    private async Task<(string Status, decimal Shortfall)> ComputeInventoryStatusAsync(int shopId)
    {
        var inventory = await db.Inventory.Where(i => i.RationShopId == shopId).ToListAsync();
        if (inventory.Count == 0)
        {
            return ("Normal", 0);
        }

        var worstShortfall = inventory.Max(i => i.MinimumStockLevel - i.AvailableQuantity);
        var isCritical = inventory.Any(i => i.AvailableQuantity <= i.MinimumStockLevel * 0.5m);
        var isLow = inventory.Any(i => i.AvailableQuantity <= i.MinimumStockLevel);

        var status = isCritical ? "Critical" : isLow ? "Low" : "Normal";
        return (status, Math.Max(0, worstShortfall));
    }
}
