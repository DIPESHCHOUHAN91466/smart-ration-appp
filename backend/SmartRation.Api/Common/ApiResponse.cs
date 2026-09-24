namespace SmartRation.Api.Common;

// Uniform envelope for every API response, per the project's response-format
// convention: { success, message, data } on success, { success, message, errors } on failure.
public class ApiResponse<T>
{
    public bool Success { get; set; }

    public string Message { get; set; } = string.Empty;

    public T? Data { get; set; }

    public IReadOnlyList<string>? Errors { get; set; }

    // Stable machine-readable reason on failures (e.g. ENTITLEMENT_EXCEEDED); null otherwise.
    [System.Text.Json.Serialization.JsonIgnore(Condition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull)]
    public string? ErrorCode { get; set; }

    public static ApiResponse<T> Ok(T data, string message = "Success") =>
        new() { Success = true, Message = message, Data = data };

    public static ApiResponse<T> Fail(string message, IReadOnlyList<string>? errors = null) =>
        new() { Success = false, Message = message, Errors = errors };
}

public class ApiResponse : ApiResponse<object?>
{
    public static ApiResponse<object?> Ok(string message = "Success") =>
        new() { Success = true, Message = message };

    public static new ApiResponse<object?> Fail(string message, IReadOnlyList<string>? errors = null) =>
        new() { Success = false, Message = message, Errors = errors };
}
