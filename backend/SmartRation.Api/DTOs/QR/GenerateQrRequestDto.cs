using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Qr;

public class GenerateQrRequestDto
{
    [Required]
    public int TokenId { get; set; }
}
