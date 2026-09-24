using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Data;
using SmartRation.Api.Services.AI;

namespace SmartRation.Api.Controllers;

// Anonymous liveness/readiness check for monitoring and the frontend's
// connectivity indicator. Reports status words only — no versions, hosts or
// connection details. The system is DEGRADED (not DOWN) when only the
// optional AI service is unavailable: the core PDS keeps working.
[ApiController]
[Route("api/health")]
[AllowAnonymous]
public class HealthController(SmartRationDbContext db, IPythonAiClient pythonAi) : ControllerBase
{
    // Root-level probe: { status, api, database, aiService } with Healthy /
    // Degraded / Unhealthy / NotConfigured. Same checks as /api/health.
    [HttpGet("/health")]
    public async Task<IActionResult> Probe(CancellationToken ct)
    {
        var database = await CanReachDatabaseAsync(ct);
        var ai = await pythonAi.IsHealthyAsync(ct);
        var body = new
        {
            status = !database ? "Unhealthy" : ai ? "Healthy" : "Degraded",
            api = "Healthy",
            database = database ? "Healthy" : "Unhealthy",
            databaseProvider = db.Database.ProviderName?.Contains("MySql", StringComparison.OrdinalIgnoreCase) == true ? "MySql" : "Sqlite",
            aiService = !pythonAi.IsConfigured ? "NotConfigured" : ai ? "Healthy" : "Unhealthy"
        };
        return database ? Ok(body) : StatusCode(StatusCodes.Status503ServiceUnavailable, body);
    }

    private async Task<bool> CanReachDatabaseAsync(CancellationToken ct)
    {
        try
        {
            return await db.Database.CanConnectAsync(ct);
        }
        catch
        {
            return false;
        }
    }

    [HttpGet]
    public async Task<IActionResult> Get(CancellationToken ct)
    {
        bool database;
        try
        {
            database = await db.Database.CanConnectAsync(ct);
        }
        catch
        {
            database = false;
        }

        var ai = await pythonAi.IsHealthyAsync(ct);

        var system = !database ? "UNHEALTHY" : ai ? "HEALTHY" : "DEGRADED";
        var body = new
        {
            system,
            api = "UP",
            database = database ? "CONNECTED" : "UNAVAILABLE",
            ai = !pythonAi.IsConfigured ? "NOT_CONFIGURED" : ai ? "AVAILABLE" : "UNAVAILABLE"
        };

        return database ? Ok(body) : StatusCode(StatusCodes.Status503ServiceUnavailable, body);
    }
}
