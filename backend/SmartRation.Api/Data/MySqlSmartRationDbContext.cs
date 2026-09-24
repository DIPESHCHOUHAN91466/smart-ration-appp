using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace SmartRation.Api.Data;

// Same model as SmartRationDbContext, used when Database:Provider = "MySql".
// A separate subclass gives MySQL its own migration history
// (Migrations/MySql) so the existing SQLite migrations stay untouched and the
// app can run on either provider. Services keep depending on
// SmartRationDbContext — Program.cs registers this type as its implementation.
public class MySqlSmartRationDbContext(DbContextOptions<MySqlSmartRationDbContext> options)
    : SmartRationDbContext(options)
{
    // Stable server version so migrations can be generated without a live
    // connection. Matches the installed MySQL 8.0 server.
    public static readonly MySqlServerVersion ServerVersion = new(new Version(8, 0, 36));

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // MySQL can't index an unbounded TEXT/LONGTEXT column. Any string that
        // takes part in a key or index and has no explicit length gets 255
        // (fits utf8mb4 index limits). SQLite has no such restriction, so this
        // lives only here.
        foreach (var entity in modelBuilder.Model.GetEntityTypes())
        {
            var indexed = entity.GetIndexes().SelectMany(i => i.Properties)
                .Concat(entity.GetKeys().SelectMany(k => k.Properties))
                .Concat(entity.GetForeignKeys().SelectMany(f => f.Properties));

            foreach (var property in indexed.Distinct())
            {
                if (property.ClrType == typeof(string) && property.GetMaxLength() is null)
                {
                    property.SetMaxLength(255);
                }
            }
        }
    }
}

// Used only by `dotnet ef migrations add --context MySqlSmartRationDbContext`.
// The connection string is a placeholder: generating migrations never connects.
public class MySqlSmartRationDbContextFactory : IDesignTimeDbContextFactory<MySqlSmartRationDbContext>
{
    public MySqlSmartRationDbContext CreateDbContext(string[] args)
    {
        var options = new DbContextOptionsBuilder<MySqlSmartRationDbContext>()
            .UseMySql("Server=localhost;Database=smartration_design", MySqlSmartRationDbContext.ServerVersion)
            .Options;
        return new MySqlSmartRationDbContext(options);
    }
}

// Exact-type factory for the default SQLite context. Without it, EF's tools
// would match the (covariant) MySQL factory above for SmartRationDbContext too
// and generate/list MySQL migrations for the SQLite history.
public class SqliteSmartRationDbContextFactory : IDesignTimeDbContextFactory<SmartRationDbContext>
{
    public SmartRationDbContext CreateDbContext(string[] args)
    {
        var options = new DbContextOptionsBuilder<SmartRationDbContext>()
            .UseSqlite("Data Source=smartration.db")
            .Options;
        return new SmartRationDbContext(options);
    }
}
