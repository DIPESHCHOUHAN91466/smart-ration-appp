namespace SmartRation.Api.Models;

// The specific commodities + quantities a beneficiary selected for one token/booking.
public class TokenItem
{
    public int Id { get; set; }

    public int TokenId { get; set; }

    public Token Token { get; set; } = null!;

    public RationType RationType { get; set; }

    public decimal Quantity { get; set; }
}
