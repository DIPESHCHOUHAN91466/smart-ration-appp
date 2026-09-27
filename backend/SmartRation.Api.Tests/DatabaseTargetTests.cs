using SmartRation.Api.Configuration;

namespace SmartRation.Api.Tests;

// The startup log line that says which database the API uses must never contain credentials.
public class DatabaseTargetTests
{
    [Fact]
    public void MySql_ShowsServerPortAndDatabase_NeverUserOrPassword()
    {
        var text = DatabaseTarget.Describe("MySql", "Server=localhost;Port=3306;Database=smartration;User=smartration_app;Password=Very$ecret-123");

        Assert.Equal("MySql, server localhost:3306, database smartration", text);
        Assert.DoesNotContain("Very$ecret-123", text);
        Assert.DoesNotContain("smartration_app", text);
    }

    [Fact]
    public void Sqlite_ShowsTheFile()
    {
        Assert.Equal("Sqlite, file smartration.db", DatabaseTarget.Describe("Sqlite", "Data Source=smartration.db"));
    }

    [Fact]
    public void MissingOrBrokenConnectionString_IsReportedWithoutEchoingIt()
    {
        Assert.Equal("MySql (no connection string)", DatabaseTarget.Describe("MySql", "  "));
        var broken = DatabaseTarget.Describe("MySql", "Password=abc;this is not a connection string");
        Assert.DoesNotContain("abc", broken);
    }

    [Fact]
    public void MissingConnectionMessage_ExplainsUserSecretsOnlyLoadInDevelopment()
    {
        var outside = DatabaseTarget.MissingMySqlConnectionMessage("Production", isDevelopment: false);
        Assert.StartsWith("Database:Provider is MySql but ConnectionStrings:MySql is not set", outside);
        Assert.Contains("environment: Production", outside);
        Assert.Contains("only read when ASPNETCORE_ENVIRONMENT=Development", outside);

        Assert.Contains("dotnet user-secrets set ConnectionStrings:MySql", DatabaseTarget.MissingMySqlConnectionMessage("Development", isDevelopment: true));
    }
}
