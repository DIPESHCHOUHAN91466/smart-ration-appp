namespace SmartRation.Api.DTOs.Government;

public class ReportSummaryDto
{
    public string ReportName { get; set; } = string.Empty;

    public string Description { get; set; } = string.Empty;

    public int RecordCount { get; set; }

    // File export (CSV/Excel/PDF) is not implemented yet — this endpoint
    // returns live aggregate counts only, for the report list screen.
    public bool ExportAvailable { get; set; } = false;
}
