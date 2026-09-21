import apiClient, { unwrap } from "./api";

export function getShops() {
  return unwrap(apiClient.get("/shops"));
}
