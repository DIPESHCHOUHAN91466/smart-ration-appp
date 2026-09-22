using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using SmartRation.Api.Configuration;
using SmartRation.Api.Data;
using SmartRation.Api.Services;
using SmartRation.Api.Services.Verification;

namespace SmartRation.Api.Tests.TestFixtures;

// Wires the REAL service implementations together against a shared
// in-memory DB and a settable fake "current user" — gives integration-level
// tests of the collection-confirmation flow without needing full ASP.NET
// Core hosting, HTTP or JWT auth.
public class TestServiceGraph(SmartRationDbContext db, FakeCurrentUserService currentUser)
{
    public FakeCurrentUserService CurrentUser { get; } = currentUser;

    public IQrService Qr { get; } = new QrService(db, Options.Create(new QrOptions { Secret = "test-secret-value-not-for-production" }), currentUser);

    public IAadhaarVerificationService Aadhaar { get; } = new SyntheticAadhaarVerificationService(db);

    public IPassbookVerificationService Passbook { get; } = new SyntheticPassbookVerificationService(db);

    public IEntitlementService Entitlement { get; } = new EntitlementService(db);

    public IAuditLogService AuditLog { get; } = new AuditLogService(db, new FakeHttpContextAccessor());

    public IVerificationAuditService VerificationAudit { get; } = new VerificationAuditService(db, new FakeHttpContextAccessor(), currentUser);

    public INotificationService Notifications { get; } = new NotificationService(db, currentUser);

    public IBeneficiaryVerificationService BuildVerificationService() =>
        new BeneficiaryVerificationService(db, Qr, Aadhaar, Passbook, Entitlement, VerificationAudit);

    public IRationCollectionService BuildCollectionService() =>
        new RationCollectionService(db, BuildVerificationService(), CurrentUser, AuditLog, VerificationAudit, Notifications, NullLogger<RationCollectionService>.Instance);
}
