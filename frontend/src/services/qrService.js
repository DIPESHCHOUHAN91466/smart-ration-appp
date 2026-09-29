import apiClient, { unwrap } from "../api/client";
import { qrLogValue } from "../features/qr/qrTiming";

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
  return apiClient.post("/qr/scan", { qrData }, { timeout: 20000 }).then((response) => {
    // Development-only: the API's own processing time (Server-Timing: app;dur=…), no payload data.
    const match = /app;dur=([\d.]+)/.exec(response.headers?.["server-timing"] ?? "");
    if (match) qrLogValue("Backend verification", `${Math.round(Number(match[1]))}ms`);
    return response.data?.data;
  });
}
