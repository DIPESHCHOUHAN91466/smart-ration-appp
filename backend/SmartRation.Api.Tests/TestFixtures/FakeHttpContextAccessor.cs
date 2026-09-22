using Microsoft.AspNetCore.Http;

namespace SmartRation.Api.Tests.TestFixtures;

public class FakeHttpContextAccessor : IHttpContextAccessor
{
    public HttpContext? HttpContext { get; set; }
}
