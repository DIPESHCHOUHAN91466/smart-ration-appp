using System.Data.Common;
using Microsoft.Extensions.Configuration;
using SmartRation.Api.Configuration;

namespace SmartRation.Api.Tests;

// The C# API accepts the Python API's DATABASE_URL and JWT_SECRET_KEY on a hosting platform.
public class SharedEnvironmentTests
{
    private static IConfiguration Config(params (string Key, string? Value)[] values) =>
        new ConfigurationBuilder().AddInMemoryCollection(values.Select(v => new KeyValuePair<string, string?>(v.Key, v.Value))).Build();

    private static DbConnectionStringBuilder Parse(string connectionString) => new() { ConnectionString = connectionString };

    [Fact]
    public void DatabaseUrl_BecomesAMySqlConnectionString_WithDecodedCredentials()
    {
        var cs = Parse(SharedEnvironment.ToMySqlConnectionString("mysql+pymysql://app%40user:p%40ss%3Aword@db.example.net:23456/smartration?charset=utf8mb4"));
        Assert.Equal("db.example.net", cs["Server"]);
        Assert.Equal("23456", cs["Port"].ToString());
        Assert.Equal("smartration", cs["Database"]);
        Assert.Equal("app@user", cs["User ID"]);
        Assert.Equal("p@ss:word", cs["Password"]);
        Assert.False(cs.ContainsKey("SslMode"));
    }

    [Theory]
    [InlineData("?ssl_ca=/tmp/mysql-ca.pem", "VerifyFull")]
    [InlineData("?ssl_ca=/tmp/mysql-ca.pem&ssl_check_hostname=false", "VerifyCA")]
    public void SslCa_TurnsOnCertificateVerification(string query, string mode)
    {
        var cs = Parse(SharedEnvironment.ToMySqlConnectionString("mysql+pymysql://u:p@h:3306/db" + query));
        Assert.Equal(mode, cs["SslMode"]);
        Assert.Equal("/tmp/mysql-ca.pem", cs["SslCa"]);
    }

    [Fact]
    public void Apply_FillsOnlyWhatIsMissing()
    {
        var config = Config(("Jwt:Key", null));
        var env = new Dictionary<string, string?> { ["DATABASE_URL"] = "mysql+pymysql://u:p@h:3306/db", ["JWT_SECRET_KEY"] = "shared-key" };
        SharedEnvironment.Apply(config, name => env.GetValueOrDefault(name));
        Assert.Equal("MySql", config["Database:Provider"]);
        Assert.Contains("Server=h", config.GetConnectionString("MySql"));
        Assert.Equal("shared-key", config["Jwt:Key"]);

        var explicitConfig = Config(("ConnectionStrings:MySql", "Server=mine"), ("Jwt:Key", "mine"), ("Database:Provider", "MySql"));
        SharedEnvironment.Apply(explicitConfig, name => env.GetValueOrDefault(name));
        Assert.Equal("Server=mine", explicitConfig.GetConnectionString("MySql"));
        Assert.Equal("mine", explicitConfig["Jwt:Key"]);
    }

    [Fact]
    public void Apply_IgnoresANonMySqlDatabaseUrl()
    {
        var config = Config();
        SharedEnvironment.Apply(config, name => name == "DATABASE_URL" ? "sqlite:///x.db" : null);
        Assert.Null(config["Database:Provider"]);
    }
}
