import apiClient, { unwrap } from "./api";

export function generateQr(tokenId) {
  return unwrap(apiClient.post("/qr/generate", { tokenId }));
}

export function verifyQr(qrCodeValue) {
  return unwrap(apiClient.post("/qr/verify", { qrCodeValue }));
}

// Signed JSON envelope for the user's own token (rendered as the QR image).
export function getQrPayload(tokenId) {
  return unwrap(apiClient.get(`/qr/payload/${tokenId}`));
}

// Global scanner pipeline: camera, uploaded image and manual entry all use
// this. Resolves to { verified, status, message, tokenNumber, verification }.
export function scanQr(qrData) {
  return unwrap(apiClient.post("/qr/scan", { qrData }, { timeout: 20000 }));
}
