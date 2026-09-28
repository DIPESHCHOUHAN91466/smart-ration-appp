import apiClient, { unwrap } from "../api/client";

export function globalSearch(query) {
  return unwrap(apiClient.get("/search", { params: { q: query } }));
}
