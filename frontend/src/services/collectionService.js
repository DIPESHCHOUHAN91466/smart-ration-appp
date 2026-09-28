import apiClient, { unwrap } from "../api/client";

export function confirmCollection(tokenId, verificationMethod) {
  return unwrap(apiClient.post("/ration/collection/confirm", { tokenId, verificationMethod }));
}

export function getCollectionHistory(beneficiaryId) {
  return unwrap(apiClient.get(`/ration/collection/history/${beneficiaryId}`));
}
