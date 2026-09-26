using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SmartRation.Api.Common;
using SmartRation.Api.DTOs.Admin;
using SmartRation.Api.Services;

namespace SmartRation.Api.Controllers;

// Backs the dashboard's top search box. Results are scoped by role server-side (SearchService) —
// a ShopOwner only ever sees their own shop's beneficiaries and tokens, never another shop's data.
[ApiController]
[Route("api/search")]
[Authorize]
public class SearchController(ISearchService search) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<ApiResponse<List<SearchResultDto>>>> Search([FromQuery] string? q) =>
        Ok(ApiResponse<List<SearchResultDto>>.Ok(await search.SearchAsync(q)));
}
