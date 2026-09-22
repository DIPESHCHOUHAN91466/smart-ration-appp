import apiClient, { unwrap } from "./api";

export function getShopMarkers(filters = {}) {
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
  return unwrap(apiClient.get("/shops/map", { params }));
}

export function getShopLocation(shopId) {
  return unwrap(apiClient.get(`/shops/${shopId}/location`));
}

export function getMapAnalytics() {
  return unwrap(apiClient.get("/government/map/analytics"));
}
