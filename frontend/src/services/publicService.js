import apiClient, { unwrap } from "./api";

// Calls the [AllowAnonymous] public endpoints — no auth token required,
// though apiClient will attach one if the viewer happens to be logged in
// (harmless, since the backend ignores it for these routes).
export function getPublicBeneficiaryProfile(publicReference) {
  return unwrap(apiClient.get(`/public/beneficiaries/${encodeURIComponent(publicReference)}`));
}
