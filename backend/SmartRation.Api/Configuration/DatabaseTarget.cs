using MySqlConnector;

namespace SmartRation.Api.Configuration;

// Safe, human-readable description of where the API's database is, for the startup log:
// provider, server, port and database name only. Never the user name or password.
public static class DatabaseTarget
{
    public static string Describe(string provider, string? connectionString)
    {
        if (string.IsNullOrWhiteSpace(connectionString))
        {
            return $"{provider} (no connection string)";
        }

        try
        {
            if (string.Equals(provider, "MySql", StringComparison.OrdinalIgnoreCase))
            {
                var mySql = new MySqlConnectionStringBuilder(connectionString);
                return $"MySql, server {mySql.Server}:{mySql.Port}, database {mySql.Database}";
            }

            var generic = new System.Data.Common.DbConnectionStringBuilder { ConnectionString = connectionString };
            return generic.TryGetValue("Data Source", out var file) ? $"{provider}, file {file}" : provider;
        }
        catch (ArgumentException)
        {
            return $"{provider} (connection string could not be parsed)";
        }
    }

    // Why ConnectionStrings:MySql can be missing, worded for the environment the API is running in.
    public static string MissingMySqlConnectionMessage(string environmentName, bool isDevelopment) =>
        $"Database:Provider is MySql but ConnectionStrings:MySql is not set (environment: {environmentName}). " +
        (isDevelopment
            ? "Set it with `dotnet user-secrets set ConnectionStrings:MySql \"Server=localhost;Port=3306;Database=smartration;User=...;Password=...\"` " +
              "(run it in backend/SmartRation.Api) or the ConnectionStrings__MySql environment variable."
            : "User secrets are only read when ASPNETCORE_ENVIRONMENT=Development. Start the API with the 'http' launch profile " +
              "(dotnet run --launch-profile http), or set the ConnectionStrings__MySql (or DATABASE_URL) environment variable.");
}
