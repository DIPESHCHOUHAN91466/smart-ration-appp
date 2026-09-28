using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;
using SmartRation.Api.Models;
using Xunit;

namespace SmartRation.Api.Tests;

// Runs the real synthetic seeder (migrations + demo data) on SQLite and checks the invariants that
// database/queries/*.sql check on a live database.
public class DbInitializerTests
{
    private static async Task<(SmartRationDbContext Db, SqliteConnection Connection)> SeededAsync()
    {
        var connection = new SqliteConnection("DataSource=:memory:");
        connection.Open();
        var db = new SmartRationDbContext(new DbContextOptionsBuilder<SmartRationDbContext>().UseSqlite(connection).Options);
        await DbInitializer.InitializeAsync(db, "test-qr-secret-0123456789abcdef-0123456789");
        return (db, connection);
    }

    [Fact]
    public async Task Cancelled_seed_tokens_do_not_hold_a_slot_place()
    {
        // Regression: the seeder counted cancelled past tokens in BookedCount, so 12 slots in the
        // development database showed places taken by nobody (found by database/queries/07_slot_count_drift.sql).
        var (db, connection) = await SeededAsync();
        using (connection)
        using (db)
        {
            var slots = await db.TimeSlots.AsNoTracking().ToListAsync();
            var liveTokens = await db.Tokens.AsNoTracking()
                .Where(t => t.Status != TokenStatus.Cancelled)
                .GroupBy(t => t.TimeSlotId)
                .Select(g => new { SlotId = g.Key, Count = g.Count() })
                .ToDictionaryAsync(x => x.SlotId, x => x.Count);

            Assert.Contains(await db.Tokens.AsNoTracking().ToListAsync(), t => t.Status == TokenStatus.Cancelled);  // the case exists
            Assert.All(slots, s => Assert.Equal(liveTokens.GetValueOrDefault(s.Id), s.BookedCount));
        }
    }

    [Fact]
    public async Task Seeded_slots_stay_within_capacity_and_masked_aadhaar_only()
    {
        var (db, connection) = await SeededAsync();
        using (connection)
        using (db)
        {
            Assert.All(await db.TimeSlots.AsNoTracking().ToListAsync(), s => Assert.InRange(s.BookedCount, 0, s.Capacity));
            Assert.All(await db.AadhaarVerifications.AsNoTracking().ToListAsync(),
                a => Assert.Matches(@"^XXXX-XXXX-\d{4}$", a.AadhaarMasked));
        }
    }
}
