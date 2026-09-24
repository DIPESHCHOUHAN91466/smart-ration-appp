namespace SmartRation.Api.DTOs.Admin;

public class SearchResultDto
{
    public string Type { get; set; } = string.Empty; // Beneficiary | Token | Shop | Scheme

    public string Title { get; set; } = string.Empty;

    public string Subtitle { get; set; } = string.Empty;

    public string Path { get; set; } = string.Empty; // frontend route to navigate to
}
