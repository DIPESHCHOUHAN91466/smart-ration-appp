using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using SmartRation.Api.Common;
using SmartRation.Api.Configuration;
using SmartRation.Api.Data;
using SmartRation.Api.Middleware;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;

var builder = WebApplication.CreateBuilder(args);

// --------------------------------------------------
// DATABASE
// --------------------------------------------------

builder.Services.AddDbContext<SmartRationDbContext>(options =>
    options.UseSqlite(
        builder.Configuration.GetConnectionString("DefaultConnection")
    ));

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
            "Jwt:Key is not set. Add it to appsettings.Development.json for local development.");
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
            "Qr:Secret is not set. Add it to appsettings.Development.json for local development.");
    }

    throw new InvalidOperationException(
        "Qr:Secret is not set. In production, set it via the Qr__Secret environment variable.");
}

builder.Services.Configure<DemoModeOptions>(builder.Configuration.GetSection(DemoModeOptions.SectionName));

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
builder.Services.AddScoped<IInventoryService, InventoryService>();
builder.Services.AddScoped<IShopService, ShopService>();
builder.Services.AddScoped<IGovernmentService, GovernmentService>();
builder.Services.AddScoped<INotificationService, NotificationService>();

// Beneficiary verification / entitlement (synthetic/demo providers — see
// Services/Verification/*.cs for the swap-in-a-real-provider architecture).
builder.Services.AddScoped<IAadhaarVerificationService, SyntheticAadhaarVerificationService>();
builder.Services.AddScoped<IPassbookVerificationService, SyntheticPassbookVerificationService>();
builder.Services.AddScoped<IOtpService, SyntheticOtpService>();
builder.Services.AddScoped<IEntitlementService, EntitlementService>();
builder.Services.AddScoped<IBeneficiaryProvisioningService, BeneficiaryProvisioningService>();
builder.Services.AddScoped<IBeneficiaryVerificationService, BeneficiaryVerificationService>();
builder.Services.AddScoped<IRationCollectionService, RationCollectionService>();
builder.Services.AddScoped<IVerificationAuditService, VerificationAuditService>();
builder.Services.AddScoped<IMapService, MapService>();

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

app.UseMiddleware<ExceptionHandlingMiddleware>();

app.UseHttpsRedirection();

app.UseCors("FrontendPolicy");

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();

public partial class Program;
