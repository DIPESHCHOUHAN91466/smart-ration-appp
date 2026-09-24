using System.Text.Json;
using SmartRation.Api.Data;
using SmartRation.Api.Models;
using SmartRation.Api.Services.Qr;
using SmartRation.Api.Tests.TestFixtures;

namespace SmartRation.Api.Tests;

// Covers the global QR scanner pipeline (POST /api/qr/scan): envelope
// parsing, project/type/field/signature/expiry validation, and the booking
// outcomes (collected, cancelled, wrong shop, unknown token).
public class QrScanServiceTests
{
    private static (TestServiceGraph Graph, QrScanService Scan) Build(SmartRationDbContext db, int shopId)
    {
        var graph = new TestServiceGraph(db, new FakeCurrentUserService { UserId = 999, Role = UserRole.ShopOwner, RationShopId = shopId });
        return (graph, new QrScanService(graph.BuildVerificationService()));
    }

    private static async Task<(string Status, bool Verified)> ScanScenario(
        Func<BasicScenario, TestServiceGraph, string> buildQr,
        TokenStatus tokenStatus = TokenStatus.Confirmed,
        int shopOffset = 0)
    {
        var (db, connection) = TestDbFactory.CreateContext();
        using (connection)
        using (db)
        {
            var scenario = ScenarioBuilder.SeedBasicScenario(db, tokenStatus: tokenStatus);
            var (graph, scan) = Build(db, scenario.Shop.Id + shopOffset);
            var result = await scan.ScanAsync(buildQr(scenario, graph));
            return (result.Status, result.Verified);
        }
    }

    private static string ValidEnvelope(BasicScenario s, TestServiceGraph g) => g.Qr.BuildSignedPayload(s.Token);

    // Re-serializes an envelope after mutating it, WITHOUT re-signing.
    private static string Mutate(string envelope, Action<Dictionary<string, string>> change)
    {
        var fields = JsonSerializer.Deserialize<Dictionary<string, string>>(envelope)!;
        change(fields);
        return JsonSerializer.Serialize(fields);
    }

    [Fact] // TEST 1
    public async Task ValidEnvelope_IsVerified()
    {
        var (status, verified) = await ScanScenario(ValidEnvelope);
        Assert.Equal(QrScanStatus.Verified, status);
        Assert.True(verified);
    }

    [Fact] // Manual entry of the bare reference goes through the same pipeline.
    public async Task BareReference_IsVerified()
    {
        var (status, _) = await ScanScenario((s, g) => g.Qr.ComputeQrValue(s.Token.Id, s.Token.TokenNumber));
        Assert.Equal(QrScanStatus.Verified, status);
    }

    [Theory] // TEST 2: random/unrelated QR codes.
    [InlineData("https://wa.me/919999999999")]
    [InlineData("upi://pay?pa=merchant@upi&am=10")]
    [InlineData("hello world")]
    [InlineData("{\"project\":\"OTHER_APP\",\"type\":\"RATION_TOKEN\"}")]
    public async Task UnrelatedQr_IsInvalidProject(string raw)
    {
        var (status, verified) = await ScanScenario((_, _) => raw);
        Assert.Equal(QrScanStatus.InvalidProject, status);
        Assert.False(verified);
    }

    [Theory] // TEST 3
    [InlineData("{not json")]
    [InlineData("[1,2,3]")]
    public async Task MalformedJson_IsInvalidFormat(string raw)
    {
        var (status, _) = await ScanScenario((_, _) => raw);
        Assert.Equal(QrScanStatus.InvalidFormat, status);
    }

    [Fact] // TEST 4
    public async Task MissingField_IsMissingFields()
    {
        var (status, _) = await ScanScenario((s, g) => Mutate(ValidEnvelope(s, g), f => f.Remove("expiresAt")));
        Assert.Equal(QrScanStatus.MissingFields, status);
    }

    [Fact] // TEST 5
    public async Task WrongType_IsInvalidType()
    {
        var (status, _) = await ScanScenario((s, g) => Mutate(ValidEnvelope(s, g), f => f["type"] = "PAYMENT"));
        Assert.Equal(QrScanStatus.InvalidType, status);
    }

    [Fact] // Tampering with any signed field (here: extending expiry) breaks the signature.
    public async Task TamperedEnvelope_IsInvalidSignature()
    {
        var (status, _) = await ScanScenario((s, g) => Mutate(ValidEnvelope(s, g), f => f["expiresAt"] = "2099-01-01T00:00:00Z"));
        Assert.Equal(QrScanStatus.InvalidSignature, status);
    }

    [Fact] // TEST 6
    public async Task ExpiredEnvelope_IsExpired()
    {
        var (status, _) = await ScanScenario((s, g) =>
        {
            s.Token.TimeSlot.SlotDate = DateTime.UtcNow.Date.AddDays(-2);
            return g.Qr.BuildSignedPayload(s.Token);
        });
        Assert.Equal(QrScanStatus.Expired, status);
    }

    [Fact] // TEST 7
    public async Task UnknownToken_IsTokenNotFound()
    {
        var (status, _) = await ScanScenario((s, g) => g.Qr.ComputeQrValue(s.Token.Id + 500, "SR-UNKNOWN"));
        Assert.Equal(QrScanStatus.TokenNotFound, status);
    }

    [Fact] // TEST 8
    public async Task CancelledBooking_IsBookingCancelled()
    {
        var (status, verified) = await ScanScenario(ValidEnvelope, TokenStatus.Cancelled);
        Assert.Equal(QrScanStatus.BookingCancelled, status);
        Assert.False(verified);
    }

    [Fact] // TEST 9
    public async Task CollectedToken_IsAlreadyCollected()
    {
        var (status, verified) = await ScanScenario(ValidEnvelope, TokenStatus.Completed);
        Assert.Equal(QrScanStatus.AlreadyCollected, status);
        Assert.False(verified);
    }

    [Fact] // TEST 10
    public async Task OtherShopsToken_IsWrongShop()
    {
        var (status, _) = await ScanScenario(ValidEnvelope, shopOffset: 999);
        Assert.Equal(QrScanStatus.WrongShop, status);
    }
}
