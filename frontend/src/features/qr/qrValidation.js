import { QR_CONTRACT, QR_REQUIRED_FIELDS, QR_STATUS } from "./qrContract";

// Fast client-side pre-check of scanned text, so obviously foreign QR codes
// (UPI, WhatsApp, URLs, random text) are rejected without a server round trip.
// This is NOT a security check: signatures, tokens, shop and booking status
// are verified only by the backend (POST /api/qr/scan).
//
// Returns { ok: true, value } or { ok: false, status }.
export function precheckQr(rawText) {
  const value = (rawText ?? "").trim();

  if (!value || value.length > QR_CONTRACT.maxLength) {
    return { ok: false, status: QR_STATUS.INVALID_FORMAT };
  }

  // Bare opaque reference (manual entry or older printed QR).
  if (!value.startsWith("{") && !value.startsWith("[")) {
    return value.startsWith(QR_CONTRACT.referencePrefix)
      ? { ok: true, value }
      : { ok: false, status: QR_STATUS.INVALID_PROJECT };
  }

  let payload;
  try {
    payload = JSON.parse(value);
  } catch {
    return { ok: false, status: QR_STATUS.INVALID_FORMAT };
  }

  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return { ok: false, status: QR_STATUS.INVALID_FORMAT };
  }
  if (payload.project !== QR_CONTRACT.project) {
    return { ok: false, status: QR_STATUS.INVALID_PROJECT };
  }
  if (QR_REQUIRED_FIELDS.some((field) => typeof payload[field] !== "string" || !payload[field].trim())) {
    return { ok: false, status: QR_STATUS.MISSING_FIELDS };
  }
  if (payload.type !== QR_CONTRACT.type) {
    return { ok: false, status: QR_STATUS.INVALID_TYPE };
  }
  if (payload.version !== QR_CONTRACT.version) {
    return { ok: false, status: QR_STATUS.UNSUPPORTED_VERSION };
  }

  // Expiry is deliberately left to the server: the signed expiresAt is only
  // meaningful once the signature is checked, and device clocks can be wrong.
  return { ok: true, value };
}
