import apiClient, { unwrap } from "./api";

export function getSlots(shopId, date) {
  return unwrap(apiClient.get("/slots", { params: { shopId, date } }));
}

export function createSlot(payload) {
  return unwrap(apiClient.post("/slots", payload));
}

export function updateSlot(id, payload) {
  return unwrap(apiClient.put(`/slots/${id}`, payload));
}
