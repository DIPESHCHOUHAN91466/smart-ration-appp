import apiClient, { unwrap } from "../api/client";

export function getSyntheticBeneficiaries(params) {
  return unwrap(apiClient.get("/admin/synthetic-data/beneficiaries", { params }));
}
