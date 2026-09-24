import apiClient, { unwrap } from "./api";

export function getMyProfile() {
  return unwrap(apiClient.get("/beneficiaries/me"));
}

export function getVerification(id) {
  return unwrap(apiClient.get(`/beneficiaries/${id}/verification`));
}

export function getFamily(id) {
  return unwrap(apiClient.get(`/beneficiaries/${id}/family`));
}

export function getEntitlement(id) {
  return unwrap(apiClient.get(`/beneficiaries/${id}/entitlement`));
}

export function getCollectionHistory(id) {
  return unwrap(apiClient.get(`/beneficiaries/${id}/collections`));
}

export function getFullProfile(id) {
  return unwrap(apiClient.get(`/beneficiaries/${id}/full-profile`));
}
