using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace SmartRation.Api.Models;

public class TimeSlot
{
    public int Id { get; set; }

    public int RationShopId { get; set; }

    public RationShop RationShop { get; set; } = null!;

    public DateTime SlotDate { get; set; }

    public TimeSpan StartTime { get; set; }

    public TimeSpan EndTime { get; set; }

    // Single-person booking as requested
    public int Capacity { get; set; } = 1;

    // Optimistic concurrency check: SaveChanges includes BookedCount in the
    // WHERE clause, so two simultaneous bookings on the last open seat can't
    // both silently succeed — the loser gets a DbUpdateConcurrencyException.
    [ConcurrencyCheck]
    public int BookedCount { get; set; } = 0;

    [NotMapped]
    public bool IsAvailable =>
        BookedCount < Capacity;
}