using SmartRation.Api.Models;
using SmartRation.Api.Services;

namespace SmartRation.Api.Tests.TestFixtures;

// Settable stand-in for the real (HttpContext-claims-based) ICurrentUserService,
// so service-layer tests can simulate "logged in as X" without real JWT auth.
public class FakeCurrentUserService : ICurrentUserService
{
    public int UserId { get; set; }

    public UserRole Role { get; set; }

    public int? RationShopId { get; set; }
}
