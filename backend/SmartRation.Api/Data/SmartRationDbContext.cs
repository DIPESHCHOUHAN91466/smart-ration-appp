using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Models;

namespace SmartRation.Api.Data;

public class SmartRationDbContext : DbContext
{
    public SmartRationDbContext(
        DbContextOptions<SmartRationDbContext> options)
        : base(options)
    {
    }

    public DbSet<User> Users => Set<User>();

    public DbSet<RationShop> RationShops => Set<RationShop>();

    public DbSet<TimeSlot> TimeSlots => Set<TimeSlot>();

    public DbSet<Token> Tokens => Set<Token>();

    public DbSet<Inventory> Inventory => Set<Inventory>();

    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // User
        modelBuilder.Entity<User>()
            .HasIndex(x => x.Email)
            .IsUnique();

        modelBuilder.Entity<User>()
            .HasIndex(x => x.MobileNumber)
            .IsUnique();

        // Shop
        modelBuilder.Entity<RationShop>()
            .HasIndex(x => x.ShopCode)
            .IsUnique();

        // User → Shop
        modelBuilder.Entity<User>()
            .HasOne(x => x.RationShop)
            .WithMany(x => x.Users)
            .HasForeignKey(x => x.RationShopId)
            .OnDelete(DeleteBehavior.SetNull);

        // Shop → TimeSlots
        modelBuilder.Entity<TimeSlot>()
            .HasOne(x => x.RationShop)
            .WithMany(x => x.TimeSlots)
            .HasForeignKey(x => x.RationShopId)
            .OnDelete(DeleteBehavior.Cascade);

        // User → Tokens
        modelBuilder.Entity<Token>()
            .HasOne(x => x.User)
            .WithMany(x => x.Tokens)
            .HasForeignKey(x => x.UserId)
            .OnDelete(DeleteBehavior.Restrict);

        // Shop → Tokens
        modelBuilder.Entity<Token>()
            .HasOne(x => x.RationShop)
            .WithMany(x => x.Tokens)
            .HasForeignKey(x => x.RationShopId)
            .OnDelete(DeleteBehavior.Restrict);

        // TimeSlot → Tokens
        modelBuilder.Entity<Token>()
            .HasOne(x => x.TimeSlot)
            .WithMany()
            .HasForeignKey(x => x.TimeSlotId)
            .OnDelete(DeleteBehavior.Restrict);

        // Token number must be unique
        modelBuilder.Entity<Token>()
            .HasIndex(x => x.TokenNumber)
            .IsUnique();

        // Inventory uniqueness
        modelBuilder.Entity<Inventory>()
            .HasIndex(x => new
            {
                x.RationShopId,
                x.RationType
            })
            .IsUnique();
    }
}