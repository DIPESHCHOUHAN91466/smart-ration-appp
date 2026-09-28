import apiClient, { unwrap } from "../api/client";

export function getShopDashboard() {
  return unwrap(apiClient.get("/shop/dashboard"));
}

export function getShopQueue() {
  return unwrap(apiClient.get("/shop/queue"));
}

export function completeCollection(tokenId) {
  return unwrap(apiClient.post("/shop/collection/complete", { tokenId }));
}
