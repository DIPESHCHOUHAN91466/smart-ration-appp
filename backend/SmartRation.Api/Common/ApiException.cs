namespace SmartRation.Api.Common;

// Base type for exceptions that should be translated into a specific HTTP
// status + ApiResponse by the global exception middleware, instead of a
// generic 500. Anything else (a real bug) still surfaces as 500.
public abstract class ApiException : Exception
{
    protected ApiException(string message) : base(message) { }

    public abstract int StatusCode { get; }

    // Optional machine-readable reason (e.g. QrScanStatus.Expired) so callers
    // like the QR scan endpoint can map a failure to a specific UI state
    // without parsing the human-readable message.
    public string? ErrorCode { get; init; }
}

public class NotFoundException(string message) : ApiException(message)
{
    public override int StatusCode => StatusCodes.Status404NotFound;
}

public class BadRequestException(string message) : ApiException(message)
{
    public override int StatusCode => StatusCodes.Status400BadRequest;
}

public class ConflictException(string message) : ApiException(message)
{
    public override int StatusCode => StatusCodes.Status409Conflict;
}

public class ForbiddenException(string message) : ApiException(message)
{
    public override int StatusCode => StatusCodes.Status403Forbidden;
}

public class ServiceUnavailableException(string message) : ApiException(message)
{
    public override int StatusCode => StatusCodes.Status503ServiceUnavailable;
}

public class UnauthorizedApiException(string message) : ApiException(message)
{
    public override int StatusCode => StatusCodes.Status401Unauthorized;
}
