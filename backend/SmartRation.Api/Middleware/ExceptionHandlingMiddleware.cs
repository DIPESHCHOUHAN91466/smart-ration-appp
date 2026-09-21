using System.Text.Json;
using SmartRation.Api.Common;

namespace SmartRation.Api.Middleware;

// Centralized error handling (Phase 17): every unhandled exception becomes
// the same { success, message, errors } JSON envelope instead of leaking a
// framework error page or a stack trace to the client.
public class ExceptionHandlingMiddleware(
    RequestDelegate next,
    ILogger<ExceptionHandlingMiddleware> logger,
    IHostEnvironment environment)
{
    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await next(context);
        }
        catch (ApiException apiException)
        {
            logger.LogWarning(apiException, "Handled API exception: {Message}", apiException.Message);
            await WriteResponseAsync(context, apiException.StatusCode, apiException.Message, null);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unhandled exception while processing {Method} {Path}", context.Request.Method, context.Request.Path);

            var errors = environment.IsDevelopment()
                ? new[] { ex.ToString() }
                : null;

            await WriteResponseAsync(
                context,
                StatusCodes.Status500InternalServerError,
                "An unexpected error occurred. Please try again later.",
                errors);
        }
    }

    private static async Task WriteResponseAsync(HttpContext context, int statusCode, string message, string[]? errors)
    {
        context.Response.ContentType = "application/json";
        context.Response.StatusCode = statusCode;

        var response = ApiResponse.Fail(message, errors);
        await context.Response.WriteAsync(JsonSerializer.Serialize(response, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        }));
    }
}
