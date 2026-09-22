using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;

namespace SmartRation.Api.Tests.TestFixtures;

// Real SQLite (not the EF InMemory provider) so tests exercise the same
// query-translation quirks as production — an open in-memory connection
// per test keeps the schema alive for the DbContext's lifetime.
public static class TestDbFactory
{
    public static (SmartRationDbContext Db, SqliteConnection Connection) CreateContext()
    {
        var connection = new SqliteConnection("DataSource=:memory:");
        connection.Open();

        var options = new DbContextOptionsBuilder<SmartRationDbContext>()
            .UseSqlite(connection)
            .Options;

        var db = new SmartRationDbContext(options);
        db.Database.EnsureCreated();

        return (db, connection);
    }
}
