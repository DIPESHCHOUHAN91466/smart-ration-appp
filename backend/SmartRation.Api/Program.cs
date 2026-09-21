using Microsoft.EntityFrameworkCore;
using SmartRation.Api.Data;

var builder = WebApplication.CreateBuilder(args);

// --------------------------------------------------
// DATABASE
// --------------------------------------------------

builder.Services.AddDbContext<SmartRationDbContext>(options =>
    options.UseSqlite(
        builder.Configuration.GetConnectionString("DefaultConnection")
    ));

// --------------------------------------------------
// CONTROLLERS
// --------------------------------------------------

builder.Services.AddControllers();

// --------------------------------------------------
// SWAGGER
// --------------------------------------------------

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

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

app.UseHttpsRedirection();

app.UseCors("FrontendPolicy");

app.UseAuthorization();

app.MapControllers();

app.Run();