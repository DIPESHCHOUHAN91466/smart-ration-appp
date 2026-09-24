import apiClient, { unwrap } from "./api";

export function globalSearch(query) {
  return unwrap(apiClient.get("/search", { params: { q: query } }));
}
