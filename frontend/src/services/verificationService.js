import apiClient, { unwrap } from "../api/client";

export function verifyByQr(reference) {
  return unwrap(apiClient.get(`/verification/qr/${encodeURIComponent(reference)}`));
}

export function requestOtp(mobileNumber) {
  return unwrap(apiClient.post("/verification/otp/request", { mobileNumber }));
}

export function verifyOtp(otpVerificationId, code) {
  return unwrap(apiClient.post("/verification/otp/verify", { otpVerificationId, code }));
}
