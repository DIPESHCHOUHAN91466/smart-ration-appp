import apiClient, { unwrap } from "./api";

export function getToken(id) {
  return unwrap(apiClient.get(`/tokens/${id}`));
}

export function getTodayQueue() {
  return unwrap(apiClient.get("/tokens/today"));
}
