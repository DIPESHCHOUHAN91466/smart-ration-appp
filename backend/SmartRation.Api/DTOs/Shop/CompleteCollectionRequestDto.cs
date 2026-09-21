using System.ComponentModel.DataAnnotations;

namespace SmartRation.Api.DTOs.Shop;

public class CompleteCollectionRequestDto
{
    [Required]
    public int TokenId { get; set; }
}
