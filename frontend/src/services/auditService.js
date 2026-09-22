import apiClient, { unwrap } from "./api";

export function getVerificationAudit(filters = {}) {
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
  return unwrap(apiClient.get("/audit/verification", { params }));
}
