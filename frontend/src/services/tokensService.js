import apiClient, { unwrap } from "../api/client";

export function getToken(id) {
  return unwrap(apiClient.get(`/tokens/${id}`));
}

export function getTodayQueue() {
  return unwrap(apiClient.get("/tokens/today"));
}
