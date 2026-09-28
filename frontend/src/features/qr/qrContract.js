// Smart Ration QR contract — mirrors backend Services/Qr/QrPayloadContract.cs.
// Change both files together.
//
// The QR image on "My Token & QR" encodes a server-signed JSON envelope:
// {
//   "version":   "1.0",
//   "project":   "SMART_RATION_HSD2C",
//   "type":      "RATION_TOKEN",
//   "reference": "SRQR-132-1606AB048DF8EE48",  // opaque HMAC-signed reference
//   "token":     "SR-2026-000132",
//   "issuedAt":  "2026-09-23T03:35:00Z",
//   "expiresAt": "2026-09-24T00:00:00Z",
//   "signature": "<server HMAC — never computed in the browser>"
// }
//
// No personal data is ever placed in the QR. To add a project-specific field,
// add it to REQUIRED_FIELDS here and to the backend contract + signature.
export const QR_CONTRACT = {
  version: "1.0",
  project: "SMART_RATION_HSD2C",
  type: "RATION_TOKEN",
  referencePrefix: "SRQR-",
  maxLength: 2048,
};

export const QR_REQUIRED_FIELDS = ["version", "project", "type", "reference", "token", "issuedAt", "expiresAt", "signature"];

// Scan outcomes. Backend statuses come from QrScanStatus; NETWORK_ERROR is client-only.
export const QR_STATUS = {
  VERIFIED: "VERIFIED",
  INVALID_FORMAT: "INVALID_FORMAT",
  INVALID_PROJECT: "INVALID_PROJECT",
  INVALID_TYPE: "INVALID_TYPE",
  MISSING_FIELDS: "MISSING_FIELDS",
  UNSUPPORTED_VERSION: "UNSUPPORTED_VERSION",
  INVALID_SIGNATURE: "INVALID_SIGNATURE",
  EXPIRED: "EXPIRED",
  TOKEN_NOT_FOUND: "TOKEN_NOT_FOUND",
  BOOKING_CANCELLED: "BOOKING_CANCELLED",
  ALREADY_COLLECTED: "ALREADY_COLLECTED",
  WRONG_SHOP: "WRONG_SHOP",
  NOT_ELIGIBLE: "NOT_ELIGIBLE",
  NETWORK_ERROR: "NETWORK_ERROR",
};

// How each outcome is presented: tone drives colour, keys are i18n keys.
export const QR_STATUS_META = {
  VERIFIED: { tone: "success", titleKey: "qr_verified", descKey: "eligible_for_collection" },
  INVALID_FORMAT: { tone: "error", titleKey: "invalid_qr", descKey: "qr_malformed_desc" },
  INVALID_PROJECT: { tone: "error", titleKey: "invalid_qr", descKey: "qr_wrong_project_desc" },
  INVALID_TYPE: { tone: "error", titleKey: "invalid_qr", descKey: "qr_wrong_type_desc" },
  MISSING_FIELDS: { tone: "error", titleKey: "qr_invalid_structure", descKey: "qr_invalid_structure_desc" },
  UNSUPPORTED_VERSION: { tone: "error", titleKey: "invalid_qr", descKey: "qr_unsupported_version_desc" },
  INVALID_SIGNATURE: { tone: "error", titleKey: "invalid_qr", descKey: "qr_invalid_signature_desc" },
  EXPIRED: { tone: "warning", titleKey: "qr_expired", descKey: "qr_expired_desc" },
  TOKEN_NOT_FOUND: { tone: "error", titleKey: "qr_not_verified", descKey: "qr_token_not_found_desc" },
  BOOKING_CANCELLED: { tone: "error", titleKey: "qr_booking_cancelled", descKey: "qr_booking_cancelled_desc" },
  ALREADY_COLLECTED: { tone: "warning", titleKey: "token_already_used", descKey: "token_already_used_desc" },
  WRONG_SHOP: { tone: "error", titleKey: "wrong_ration_shop", descKey: "wrong_ration_shop_desc" },
  NOT_ELIGIBLE: { tone: "warning", titleKey: "qr_not_eligible", descKey: null },
  NETWORK_ERROR: { tone: "error", titleKey: "qr_network_error", descKey: "qr_network_error_desc" },
};
