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

    // For provider-specific subclasses (MySqlSmartRationDbContext), which keep
    // their own migration history alongside the SQLite one.
    protected SmartRationDbContext(DbContextOptions options)
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

    public DbSet<Beneficiary> Beneficiaries => Set<Beneficiary>();

    public DbSet<Family> Families => Set<Family>();

    public DbSet<FamilyMember> FamilyMembers => Set<FamilyMember>();

    public DbSet<AadhaarVerification> AadhaarVerifications => Set<AadhaarVerification>();

    public DbSet<PassbookVerification> PassbookVerifications => Set<PassbookVerification>();

    public DbSet<MobileVerification> MobileVerifications => Set<MobileVerification>();

    public DbSet<RationScheme> RationSchemes => Set<RationScheme>();

    public DbSet<SchemeEntitlementItem> SchemeEntitlementItems => Set<SchemeEntitlementItem>();

    public DbSet<RationCollection> RationCollections => Set<RationCollection>();

    public DbSet<RationCollectionItem> RationCollectionItems => Set<RationCollectionItem>();

    public DbSet<VerificationAuditLog> VerificationAuditLogs => Set<VerificationAuditLog>();

    public DbSet<InventoryMovement> InventoryMovements => Set<InventoryMovement>();

    public DbSet<OtpVerification> OtpVerifications => Set<OtpVerification>();

    public DbSet<AIInsight> AIInsights => Set<AIInsight>();

    public DbSet<AIAlert> AIAlerts => Set<AIAlert>();

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

        // RationScheme
        modelBuilder.Entity<RationScheme>()
            .HasIndex(x => x.SchemeCode)
            .IsUnique();

        modelBuilder.Entity<SchemeEntitlementItem>()
            .HasOne(x => x.RationScheme)
            .WithMany(x => x.EntitlementItems)
            .HasForeignKey(x => x.RationSchemeId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<SchemeEntitlementItem>()
            .HasIndex(x => new { x.RationSchemeId, x.RationType })
            .IsUnique();

        // Family
        modelBuilder.Entity<Family>()
            .HasIndex(x => x.FamilyCode)
            .IsUnique();

        modelBuilder.Entity<Family>()
            .HasOne(x => x.RationShop)
            .WithMany(x => x.Families)
            .HasForeignKey(x => x.RationShopId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<Family>()
            .HasOne(x => x.RationScheme)
            .WithMany(x => x.Families)
            .HasForeignKey(x => x.RationSchemeId)
            .OnDelete(DeleteBehavior.Restrict);

        // Family → FamilyMembers
        modelBuilder.Entity<FamilyMember>()
            .HasOne(x => x.Family)
            .WithMany(x => x.Members)
            .HasForeignKey(x => x.FamilyId)
            .OnDelete(DeleteBehavior.Cascade);

        // Beneficiary
        modelBuilder.Entity<Beneficiary>()
            .HasIndex(x => x.BeneficiaryCode)
            .IsUnique();

        modelBuilder.Entity<Beneficiary>()
            .HasIndex(x => x.UserId)
            .IsUnique();

        modelBuilder.Entity<Beneficiary>()
            .HasOne(x => x.User)
            .WithOne(x => x.Beneficiary)
            .HasForeignKey<Beneficiary>(x => x.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<Beneficiary>()
            .HasOne(x => x.Family)
            .WithMany(x => x.Beneficiaries)
            .HasForeignKey(x => x.FamilyId)
            .OnDelete(DeleteBehavior.Restrict);

        // Beneficiary → verification records (each optional 1:1)
        modelBuilder.Entity<AadhaarVerification>()
            .HasIndex(x => x.BeneficiaryId)
            .IsUnique();

        modelBuilder.Entity<AadhaarVerification>()
            .HasOne(x => x.Beneficiary)
            .WithOne(x => x.AadhaarVerification)
            .HasForeignKey<AadhaarVerification>(x => x.BeneficiaryId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<PassbookVerification>()
            .HasIndex(x => x.BeneficiaryId)
            .IsUnique();

        modelBuilder.Entity<PassbookVerification>()
            .HasOne(x => x.Beneficiary)
            .WithOne(x => x.PassbookVerification)
            .HasForeignKey<PassbookVerification>(x => x.BeneficiaryId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<MobileVerification>()
            .HasIndex(x => x.BeneficiaryId)
            .IsUnique();

        modelBuilder.Entity<MobileVerification>()
            .HasOne(x => x.Beneficiary)
            .WithOne(x => x.MobileVerification)
            .HasForeignKey<MobileVerification>(x => x.BeneficiaryId)
            .OnDelete(DeleteBehavior.Cascade);

        // RationCollection
        modelBuilder.Entity<RationCollection>()
            .HasIndex(x => x.CollectionCode)
            .IsUnique();

        modelBuilder.Entity<RationCollection>()
            .HasIndex(x => x.TokenId)
            .IsUnique();

        // A client retrying a confirm over a flaky network sends the same key;
        // the unique index makes a duplicate insert impossible even under a race.
        modelBuilder.Entity<RationCollection>()
            .Property(x => x.IdempotencyKey)
            .HasMaxLength(64);

        modelBuilder.Entity<RationCollection>()
            .HasIndex(x => x.IdempotencyKey)
            .IsUnique();

        modelBuilder.Entity<InventoryMovement>()
            .HasOne(x => x.RationShop)
            .WithMany()
            .HasForeignKey(x => x.RationShopId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<InventoryMovement>()
            .HasIndex(x => new { x.RationShopId, x.RationType, x.CreatedAt });

        modelBuilder.Entity<AIAlert>(e =>
        {
            e.Property(x => x.Source).HasMaxLength(32).HasDefaultValue("RULES");
            e.Property(x => x.AlertType).HasMaxLength(64);
            e.Property(x => x.Title).HasMaxLength(200);
            e.Property(x => x.DedupKey).HasMaxLength(128);
            e.Property(x => x.RecommendedAction).HasMaxLength(500);
            e.Property(x => x.ResolutionNote).HasMaxLength(500);
            e.HasIndex(x => new { x.DedupKey, x.Status });
            e.HasIndex(x => new { x.ShopId, x.Status });
        });

        modelBuilder.Entity<AuditLog>(e =>
        {
            e.Property(x => x.Role).HasMaxLength(32);
            e.Property(x => x.Result).HasMaxLength(16);
        });

        modelBuilder.Entity<InventoryMovement>()
            .Property(x => x.Reference)
            .HasMaxLength(64);

        modelBuilder.Entity<InventoryMovement>()
            .Property(x => x.Note)
            .HasMaxLength(256);

        modelBuilder.Entity<RationCollection>()
            .HasOne(x => x.Token)
            .WithOne(x => x.Collection)
            .HasForeignKey<RationCollection>(x => x.TokenId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<RationCollection>()
            .HasOne(x => x.Beneficiary)
            .WithMany()
            .HasForeignKey(x => x.BeneficiaryId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<RationCollection>()
            .HasOne(x => x.RationShop)
            .WithMany()
            .HasForeignKey(x => x.RationShopId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<RationCollectionItem>()
            .HasOne(x => x.RationCollection)
            .WithMany(x => x.Items)
            .HasForeignKey(x => x.RationCollectionId)
            .OnDelete(DeleteBehavior.Cascade);

        // OtpVerification
        modelBuilder.Entity<OtpVerification>()
            .HasOne(x => x.Beneficiary)
            .WithMany()
            .HasForeignKey(x => x.BeneficiaryId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}