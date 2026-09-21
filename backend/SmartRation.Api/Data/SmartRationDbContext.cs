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

    public DbSet<RefreshToken> RefreshTokens => Set<RefreshToken>();

    public DbSet<Notification> Notifications => Set<Notification>();

    public DbSet<RationItem> RationItems => Set<RationItem>();

    public DbSet<TokenItem> TokenItems => Set<TokenItem>();

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

        // Token → TokenItems
        modelBuilder.Entity<TokenItem>()
            .HasOne(x => x.Token)
            .WithMany(x => x.Items)
            .HasForeignKey(x => x.TokenId)
            .OnDelete(DeleteBehavior.Cascade);

        // RationItem catalog uniqueness
        modelBuilder.Entity<RationItem>()
            .HasIndex(x => x.RationType)
            .IsUnique();

        // User → RefreshTokens
        modelBuilder.Entity<RefreshToken>()
            .HasOne(x => x.User)
            .WithMany(x => x.RefreshTokens)
            .HasForeignKey(x => x.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<RefreshToken>()
            .HasIndex(x => x.TokenHash)
            .IsUnique();

        // User → Notifications
        modelBuilder.Entity<Notification>()
            .HasOne(x => x.User)
            .WithMany(x => x.Notifications)
            .HasForeignKey(x => x.UserId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}