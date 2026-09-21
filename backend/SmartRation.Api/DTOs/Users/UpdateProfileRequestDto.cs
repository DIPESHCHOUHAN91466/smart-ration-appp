using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Users;

public class UpdateProfileRequestDto
{
    [Required, StringLength(150, MinimumLength = 2)]
    public string FullName { get; set; } = string.Empty;

    [Required, Phone, StringLength(20)]
    public string MobileNumber { get; set; } = string.Empty;
}
