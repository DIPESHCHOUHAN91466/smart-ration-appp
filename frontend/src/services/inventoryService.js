import apiClient, { unwrap } from "../api/client";

export function getInventory(shopId) {
  return unwrap(apiClient.get("/inventory", { params: shopId ? { shopId } : {} }));
}

export function createInventory(payload) {
  return unwrap(apiClient.post("/inventory", payload));
}

export function updateInventory(id, payload) {
  return unwrap(apiClient.put(`/inventory/${id}`, payload));
}
