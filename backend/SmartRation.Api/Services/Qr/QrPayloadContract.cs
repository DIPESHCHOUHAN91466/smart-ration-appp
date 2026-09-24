namespace SmartRation.Api.Services.Qr;

// Single source of truth for the Smart Ration QR envelope. The frontend
// mirrors these values in src/qr/qrContract.js — change both together.
//
// Envelope (JSON, encoded into the QR image shown on "My Token & QR"):
// {
//   "version":   "1.0",
//   "project":   "SMART_RATION_HSD2C",
//   "type":      "RATION_TOKEN",
//   "reference": "SRQR-132-1606AB048DF8EE48",   // existing HMAC-signed opaque reference
//   "token":     "SR-2026-000132",
//   "issuedAt":  "2026-09-23T03:35:00Z",
//   "expiresAt": "2026-09-24T00:00:00Z",
//   "signature": "<HMAC-SHA256 hex over the fields above>"
// }
//
// The envelope never carries personal data (no name, Aadhaar, mobile): the
// server resolves everything else from the database after verifying the
// signature. To add a project-specific field: add it to RequiredFields, to
// the canonical string in QrService.SignEnvelope, and to the frontend contract.
public static class QrPayloadContract
{
    public const string Version = "1.0";
    public const string Project = "SMART_RATION_HSD2C";
    public const string Type = "RATION_TOKEN";

    public static readonly string[] RequiredFields =
        ["version", "project", "type", "reference", "token", "issuedAt", "expiresAt", "signature"];
}

// Machine-readable outcomes of a scan, shared with the frontend scanner.
public static class QrScanStatus
{
    public const string Verified = "VERIFIED";
    public const string InvalidFormat = "INVALID_FORMAT";
    public const string InvalidProject = "INVALID_PROJECT";
    public const string InvalidType = "INVALID_TYPE";
    public const string MissingFields = "MISSING_FIELDS";
    public const string UnsupportedVersion = "UNSUPPORTED_VERSION";
    public const string InvalidSignature = "INVALID_SIGNATURE";
    public const string Expired = "EXPIRED";
    public const string TokenNotFound = "TOKEN_NOT_FOUND";
    public const string BookingCancelled = "BOOKING_CANCELLED";
    public const string AlreadyCollected = "ALREADY_COLLECTED";
    public const string WrongShop = "WRONG_SHOP";
    public const string NotEligible = "NOT_ELIGIBLE";
}

// Result of parsing raw scanned text: the opaque reference to resolve, plus
// the token number the envelope claimed (null for a bare SRQR reference).
public record ParsedQr(string Reference, string? ClaimedTokenNumber);
