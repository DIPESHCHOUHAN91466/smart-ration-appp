using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Auth;

public class RefreshRequestDto
{
    [Required]
    public string RefreshToken { get; set; } = string.Empty;
}
