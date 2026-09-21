using SmartRation.Api.DTOs.Government;

namespace SmartRation.Api.Services;

public interface IGovernmentService
{
    Task<GovernmentDashboardDto> GetDashboardAsync();

    Task<StatisticsDto> GetStatisticsAsync(DateTime? fromDate, DateTime? toDate);

    Task<IReadOnlyList<ReportSummaryDto>> GetReportsAsync(DateTime? fromDate, DateTime? toDate);
}
