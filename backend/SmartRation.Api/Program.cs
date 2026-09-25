using System.Text;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Data;
using SmartRation.Api.Middleware;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;
using SmartRation.Api.Services.AI;
using SmartRation.Api.Services.Qr;
using SmartRation.Api.Services.Sms;

var builder = WebApplication.CreateBuilder(args);

// --------------------------------------------------
// DATABASE
// --------------------------------------------------

// Database:Provider selects the engine: "Sqlite" (default, zero setup) or
// "MySql". MySQL's connection string comes from ConnectionStrings:MySql —
// set it via user-secrets or the ConnectionStrings__MySql environment
// variable, never in a committed appsettings file.
var databaseProvider = builder.Configuration["Database:Provider"] ?? "Sqlite";

if (string.Equals(databaseProvider, "MySql", StringComparison.OrdinalIgnoreCase))
{
    var mySqlConnection = builder.Configuration.GetConnectionString("MySql");
    if (string.IsNullOrWhiteSpace(mySqlConnection))
    {
        throw new InvalidOperationException(
            "Database:Provider is MySql but ConnectionStrings:MySql is not set. Set it with " +
            "`dotnet user-secrets set ConnectionStrings:MySql \"Server=localhost;Database=smartration;User=...;Password=...\"` " +
            "or the ConnectionStrings__MySql environment variable.");
    }

    // No EnableRetryOnFailure: RationCollectionService opens its own
    // transaction, which a retrying execution strategy doesn't allow.
    builder.Services.AddDbContext<SmartRationDbContext, MySqlSmartRationDbContext>(options =>
        options.UseMySql(mySqlConnection, MySqlSmartRationDbContext.ServerVersion));
}
else
{
    builder.Services.AddDbContext<SmartRationDbContext>(options =>
        options.UseSqlite(
            builder.Configuration.GetConnectionString("DefaultConnection")
        ));
}

// --------------------------------------------------
// JWT CONFIGURATION
// --------------------------------------------------

builder.Services.Configure<JwtOptions>(builder.Configuration.GetSection(JwtOptions.SectionName));

var jwtOptions = builder.Configuration.GetSection(JwtOptions.SectionName).Get<JwtOptions>()
    ?? throw new InvalidOperationException("Jwt configuration section is missing.");

if (string.IsNullOrWhiteSpace(jwtOptions.Key))
{
    if (builder.Environment.IsDevelopment())
    {
        throw new InvalidOperationException(
            "Jwt:Key is not set. For local development run: dotnet user-secrets set \"Jwt:Key\" \"<64+ random chars>\" (see README).");
    }

    throw new InvalidOperationException(
        "Jwt:Key is not set. In production, set it via the Jwt__Key environment variable — never commit a real signing key to source control.");
}

builder.Services.Configure<QrOptions>(builder.Configuration.GetSection(QrOptions.SectionName));

var qrOptions = builder.Configuration.GetSection(QrOptions.SectionName).Get<QrOptions>()
    ?? throw new InvalidOperationException("Qr configuration section is missing.");

if (string.IsNullOrWhiteSpace(qrOptions.Secret))
{
    if (builder.Environment.IsDevelopment())
    {
        throw new InvalidOperationException(
            "Qr:Secret is not set. For local development run: dotnet user-secrets set \"Qr:Secret\" \"<64+ random chars>\" (see README). Changing it invalidates every issued QR code.");
    }

    throw new InvalidOperationException(
        "Qr:Secret is not set. In production, set it via the Qr__Secret environment variable.");
}

builder.Services.Configure<DemoModeOptions>(builder.Configuration.GetSection(DemoModeOptions.SectionName));
builder.Services.Configure<SmsOptions>(builder.Configuration.GetSection(SmsOptions.SectionName));

var demoOptions = builder.Configuration.GetSection(DemoModeOptions.SectionName).Get<DemoModeOptions>() ?? new DemoModeOptions();
var smsOptions = builder.Configuration.GetSection(SmsOptions.SectionName).Get<SmsOptions>() ?? new SmsOptions();

// Production must never silently fall back to a fixed demo OTP or a mock SMS
// provider that sends nothing. Fail fast at startup instead.
if (!builder.Environment.IsDevelopment())
{
    if (demoOptions.DemoOtpEnabled)
    {
        throw new InvalidOperationException("Demo:DemoOtpEnabled must be false outside Development (set Demo__DemoOtpEnabled=false).");
    }
    if (!string.Equals(smsOptions.Provider, "Http", StringComparison.OrdinalIgnoreCase))
    {
        throw new InvalidOperationException("Sms:Provider must be 'Http' (a real gateway) outside Development.");
    }
}

// --------------------------------------------------
// AUTHENTICATION / AUTHORIZATION
// --------------------------------------------------

builder.Services
    .AddAuthentication(options =>
    {
        options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
        options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
    })
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = jwtOptions.Issuer,
            ValidateAudience = true,
            ValidAudience = jwtOptions.Audience,
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtOptions.Key)),
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromSeconds(30)
        };

        // Return our standard ApiResponse envelope instead of an empty 401/403 body.
        options.Events = new JwtBearerEvents
        {
            OnChallenge = async context =>
            {
                context.HandleResponse();
                context.Response.StatusCode = StatusCodes.Status401Unauthorized;
                context.Response.ContentType = "application/json";
                await context.Response.WriteAsJsonAsync(ApiResponse.Fail("Authentication required."));
            },
            OnForbidden = async context =>
            {
                context.Response.StatusCode = StatusCodes.Status403Forbidden;
                context.Response.ContentType = "application/json";
                await context.Response.WriteAsJsonAsync(ApiResponse.Fail("You do not have permission to perform this action."));
            }
        };
    });

builder.Services.AddAuthorization();

// --------------------------------------------------
// APPLICATION SERVICES
// --------------------------------------------------

builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<IJwtService, JwtService>();
builder.Services.AddScoped<ICurrentUserService, CurrentUserService>();
builder.Services.AddScoped<IAuditLogService, AuditLogService>();
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IBookingService, BookingService>();
builder.Services.AddScoped<ISlotService, SlotService>();
builder.Services.AddScoped<IQrService, QrService>();

// Optional Python AI analytics service. Short timeout: the core PDS never waits on it.
builder.Services.Configure<AiServiceOptions>(builder.Configuration.GetSection(AiServiceOptions.SectionName));
builder.Services.AddHttpClient<IPythonAiClient, PythonAiClient>((sp, client) =>
{
    var ai = sp.GetRequiredService<Microsoft.Extensions.Options.IOptions<AiServiceOptions>>().Value;
    if (!string.IsNullOrWhiteSpace(ai.BaseUrl))
    {
        client.BaseAddress = new Uri(ai.BaseUrl);
    }
    client.Timeout = TimeSpan.FromSeconds(Math.Clamp(ai.TimeoutSeconds, 1, 30));
});
builder.Services.AddScoped<IQrScanService, QrScanService>();
builder.Services.AddScoped<IAiAlertService, AiAlertService>();
builder.Services.AddScoped<IInventoryService, InventoryService>();
builder.Services.AddScoped<IShopService, ShopService>();
builder.Services.AddScoped<IGovernmentService, GovernmentService>();
builder.Services.AddScoped<INotificationService, NotificationService>();

// Beneficiary verification / entitlement (synthetic/demo providers — see
// Services/Verification/*.cs for the swap-in-a-real-provider architecture).
builder.Services.AddScoped<IAadhaarVerificationService, SyntheticAadhaarVerificationService>();
builder.Services.AddScoped<IPassbookVerificationService, SyntheticPassbookVerificationService>();
builder.Services.AddScoped<IOtpService, SyntheticOtpService>();
if (string.Equals(smsOptions.Provider, "Http", StringComparison.OrdinalIgnoreCase))
{
    builder.Services.AddHttpClient<ISmsProvider, HttpSmsProvider>(c => c.Timeout = TimeSpan.FromSeconds(10));
}
else
{
    builder.Services.AddSingleton<ISmsProvider, MockSmsProvider>();
}
builder.Services.AddScoped<IEntitlementService, EntitlementService>();
builder.Services.AddScoped<IBeneficiaryProvisioningService, BeneficiaryProvisioningService>();
builder.Services.AddScoped<IBeneficiaryVerificationService, BeneficiaryVerificationService>();
builder.Services.AddScoped<IRationCollectionService, RationCollectionService>();
builder.Services.AddScoped<IVerificationAuditService, VerificationAuditService>();
builder.Services.AddScoped<IMapService, MapService>();

// AI Intelligence Center — rule-based statistical services (see Services/AI/*.cs).
builder.Services.AddScoped<IDemandForecastService, DemandForecastService>();
builder.Services.AddScoped<IInventoryRiskService, InventoryRiskService>();
builder.Services.AddScoped<IQueuePredictionService, QueuePredictionService>();
builder.Services.AddScoped<IAnomalyDetectionService, AnomalyDetectionService>();
builder.Services.AddScoped<IShopInsightService, ShopInsightService>();
builder.Services.AddScoped<IBeneficiaryInsightService, BeneficiaryInsightService>();
builder.Services.AddScoped<IAIIntelligenceService, AIIntelligenceService>();

// --------------------------------------------------
// CONTROLLERS
// --------------------------------------------------

builder.Services
    .AddControllers()
    .ConfigureApiBehaviorOptions(options =>
    {
        // Uniform { success, message, errors } envelope for model-validation failures too.
        options.InvalidModelStateResponseFactory = context =>
        {
            var errors = context.ModelState
                .Where(kvp => kvp.Value?.Errors.Count > 0)
                .SelectMany(kvp => kvp.Value!.Errors.Select(e => $"{kvp.Key}: {e.ErrorMessage}"))
                .ToList();

            return new BadRequestObjectResult(ApiResponse.Fail("One or more validation errors occurred.", errors));
        };
    });

// --------------------------------------------------
// SWAGGER
// --------------------------------------------------

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "Smart Ration HSD2C API",
        Version = "v1",
        Description = "Government-oriented smart ration distribution management API."
    });

    var jwtScheme = new Microsoft.OpenApi.Models.OpenApiSecurityScheme
    {
        Scheme = "bearer",
        BearerFormat = "JWT",
        Name = "Authorization",
        In = Microsoft.OpenApi.Models.ParameterLocation.Header,
        Type = Microsoft.OpenApi.Models.SecuritySchemeType.Http,
        Description = "Enter the access token returned by /api/auth/login."
    };
    options.AddSecurityDefinition("Bearer", jwtScheme);
    options.AddSecurityRequirement(new Microsoft.OpenApi.Models.OpenApiSecurityRequirement
    {
        { new Microsoft.OpenApi.Models.OpenApiSecurityScheme { Reference = new Microsoft.OpenApi.Models.OpenApiReference { Type = Microsoft.OpenApi.Models.ReferenceType.SecurityScheme, Id = "Bearer" } }, [] }
    });
});

// --------------------------------------------------
// CORS
// --------------------------------------------------

builder.Services.AddCors(options =>
{
    options.AddPolicy("FrontendPolicy", policy =>
    {
        policy
            .WithOrigins(
                "http://localhost:5173"
            )
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});

// --------------------------------------------------
// RATE LIMITING (per client IP)
// --------------------------------------------------

builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.OnRejected = async (context, ct) =>
    {
        context.HttpContext.Response.ContentType = "application/json";
        await context.HttpContext.Response.WriteAsJsonAsync(
            ApiResponse.Fail("Too many requests. Please wait a moment and try again."), ct);
    };

    RateLimitPartition<string> PerIp(HttpContext http, int permits, TimeSpan window) =>
        RateLimitPartition.GetFixedWindowLimiter(
            http.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            _ => new FixedWindowRateLimiterOptions { PermitLimit = permits, Window = window, QueueLimit = 0 });

    // Brute-force protection for credentials and OTP codes.
    options.AddPolicy("auth", http => PerIp(http, 10, TimeSpan.FromMinutes(1)));
    options.AddPolicy("otp", http => PerIp(http, 6, TimeSpan.FromMinutes(1)));
    // A busy counter scans often; this only stops scripted probing.
    options.AddPolicy("scan", http => PerIp(http, 120, TimeSpan.FromMinutes(1)));
});

var app = builder.Build();

// --------------------------------------------------
// DATABASE MIGRATION + SEED
// --------------------------------------------------

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<SmartRationDbContext>();
    await DbInitializer.InitializeAsync(db, qrOptions.Secret);
}

// --------------------------------------------------
// DEVELOPMENT SWAGGER
// --------------------------------------------------

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// --------------------------------------------------
// MIDDLEWARE
// --------------------------------------------------

// Requests forwarded by the Python backend's proxy arrive from 127.0.0.1. Take the client
// address from X-Forwarded-For so per-IP rate limits and audit IPs see the real client.
// Only loopback proxies are trusted (ASP.NET default), so remote callers can't spoof it.
app.UseForwardedHeaders(new ForwardedHeadersOptions { ForwardedHeaders = ForwardedHeaders.XForwardedFor });

app.UseMiddleware<ExceptionHandlingMiddleware>();

app.UseHttpsRedirection();

app.UseCors("FrontendPolicy");

app.UseRateLimiter();

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();

public partial class Program;
