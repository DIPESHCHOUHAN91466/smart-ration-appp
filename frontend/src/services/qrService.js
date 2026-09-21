import apiClient, { unwrap } from "./api";

export function generateQr(tokenId) {
  return unwrap(apiClient.post("/qr/generate", { tokenId }));
}

export function verifyQr(qrCodeValue) {
  return unwrap(apiClient.post("/qr/verify", { qrCodeValue }));
}
