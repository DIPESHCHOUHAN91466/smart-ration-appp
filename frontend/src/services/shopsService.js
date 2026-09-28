import apiClient, { unwrap } from "../api/client";

export function getShops() {
  return unwrap(apiClient.get("/shops"));
}
