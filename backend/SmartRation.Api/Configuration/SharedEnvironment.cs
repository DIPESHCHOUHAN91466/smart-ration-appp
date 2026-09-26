namespace SmartRation.Api.Configuration;

// Lets the C# API run from the SAME environment variables as the Python API, so a hosting platform
// (Render, Railway, ...) needs one shared group instead of two formats of the same secret:
//   DATABASE_URL    mysql+pymysql://user:password@host:3306/db?ssl_ca=/tmp/mysql-ca.pem
//                   -> ConnectionStrings:MySql (+ Database:Provider=MySql)
//   JWT_SECRET_KEY  -> Jwt:Key
// Explicit C# settings (ConnectionStrings__MySql, Jwt__Key, user-secrets) always win.
public static class SharedEnvironment
{
    public static void Apply(IConfiguration configuration, Func<string, string?> getEnvironment)
    {
        var databaseUrl = getEnvironment("DATABASE_URL");
        if (string.IsNullOrWhiteSpace(configuration.GetConnectionString("MySql")) && !string.IsNullOrWhiteSpace(databaseUrl)
            && databaseUrl.StartsWith("mysql", StringComparison.OrdinalIgnoreCase))
        {
            configuration["ConnectionStrings:MySql"] = ToMySqlConnectionString(databaseUrl);
            configuration["Database:Provider"] = "MySql";
        }
        var jwtKey = getEnvironment("JWT_SECRET_KEY");
        if (string.IsNullOrWhiteSpace(configuration["Jwt:Key"]) && !string.IsNullOrWhiteSpace(jwtKey))
        {
            configuration["Jwt:Key"] = jwtKey;
        }
    }

    // mysql[+driver]://user:password@host[:port]/database[?ssl_ca=path&ssl_check_hostname=false]
    public static string ToMySqlConnectionString(string databaseUrl)
    {
        var uri = new Uri(databaseUrl.Replace("mysql+pymysql://", "mysql://", StringComparison.OrdinalIgnoreCase));
        var userInfo = uri.UserInfo.Split(':', 2);
        var user = Uri.UnescapeDataString(userInfo[0]);
        var password = userInfo.Length > 1 ? Uri.UnescapeDataString(userInfo[1]) : string.Empty;
        var database = Uri.UnescapeDataString(uri.AbsolutePath.Trim('/'));
        var query = uri.Query.TrimStart('?').Split('&', StringSplitOptions.RemoveEmptyEntries)
            .Select(p => p.Split('=', 2))
            .ToDictionary(p => Uri.UnescapeDataString(p[0]), p => p.Length > 1 ? Uri.UnescapeDataString(p[1]) : string.Empty,
                          StringComparer.OrdinalIgnoreCase);

        var builder = new System.Data.Common.DbConnectionStringBuilder
        {
            ["Server"] = uri.Host,
            ["Port"] = uri.Port > 0 ? uri.Port : 3306,
            ["Database"] = database,
            ["User ID"] = user,
            ["Password"] = password,
        };
        if (query.TryGetValue("ssl_ca", out var ca) && ca.Length > 0)
        {
            // Verify the server certificate against the provider's CA; also its host name unless disabled.
            var checkHost = !query.TryGetValue("ssl_check_hostname", out var check) || !string.Equals(check, "false", StringComparison.OrdinalIgnoreCase);
            builder["SslMode"] = checkHost ? "VerifyFull" : "VerifyCA";
            builder["SslCa"] = ca;
        }
        return builder.ConnectionString;
    }
}
