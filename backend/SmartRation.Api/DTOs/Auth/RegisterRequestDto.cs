using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Auth;

// Public self-registration always creates a Rural User account — any
// higher-privilege role must be provisioned separately by an administrator,
// never granted from client-supplied input.
public class RegisterRequestDto
{
    [Required, StringLength(150, MinimumLength = 2)]
    public string FullName { get; set; } = string.Empty;

    [Required, EmailAddress, StringLength(200)]
    public string Email { get; set; } = string.Empty;

    [Required, Phone, StringLength(20)]
    public string MobileNumber { get; set; } = string.Empty;

    [Required, StringLength(100, MinimumLength = 8)]
    public string Password { get; set; } = string.Empty;
}
