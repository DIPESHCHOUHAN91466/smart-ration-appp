import apiClient, { unwrap } from "./api";

export function getIntelligenceCenter() {
  return unwrap(apiClient.get("/ai/intelligence-center"));
}

export function getDemandForecast(shopId) {
  return unwrap(apiClient.get("/ai/demand-forecast", { params: shopId ? { shopId } : {} }));
}

export function getInventoryRisk(shopId) {
  return unwrap(apiClient.get("/ai/inventory-risk", { params: shopId ? { shopId } : {} }));
}

export function getQueuePrediction(shopId) {
  return unwrap(apiClient.get("/ai/queue-prediction", { params: shopId ? { shopId } : {} }));
}

export function getAlerts() {
  return unwrap(apiClient.get("/ai/alerts"));
}

export function getShopInsight(shopId) {
  return unwrap(apiClient.get(`/ai/shops/${shopId}/insight`));
}

export function getBeneficiaryInsight(beneficiaryId) {
  return unwrap(apiClient.get(`/ai/beneficiaries/${beneficiaryId}/insight`));
}

// ---- Python AI analytics (optional service). Each resolves to
// { available, source: "python-ai" | "fallback" | "unavailable", data, fallback, errorCode, message }.

export function getAnalyticsForecast({ shopId, horizonDays = 7, lang = "en" } = {}) {
  return unwrap(apiClient.get("/ai/analytics/forecast", { params: { shopId, horizonDays, lang } }));
}

export function getAnalyticsInventory({ shopId, lang = "en" } = {}) {
  return unwrap(apiClient.get("/ai/analytics/inventory", { params: { shopId, lang } }));
}

export function getAnalyticsQueue({ shopId, lang = "en" } = {}) {
  return unwrap(apiClient.get("/ai/analytics/queue", { params: { shopId, lang } }));
}

export function getAnalyticsRisk({ shopId, limit = 10, lang = "en" } = {}) {
  return unwrap(apiClient.get("/ai/analytics/risk", { params: { shopId, limit, lang } }));
}

export function getAnalyticsShops({ shopId, lang = "en" } = {}) {
  return unwrap(apiClient.get("/ai/analytics/shops", { params: { shopId, lang } }));
}

export function getSystemHealth() {
  return apiClient.get("/health", { validateStatus: () => true }).then((r) => r.data);
}

// ---- Persisted AI alerts (built-in rules + Python AI) ----

// Open + under-review alerts; also triggers a throttled, deduplicated re-analysis.
export function getActiveAlerts({ shopId } = {}) {
  return unwrap(apiClient.get("/ai/alerts/active", { params: { shopId } }));
}

export function listAlerts({ status = "all", shopId, source, limit = 100 } = {}) {
  return unwrap(apiClient.get("/ai/alerts/list", { params: { status, shopId, source, limit } }));
}

export function getAlert(id) {
  return unwrap(apiClient.get(`/ai/alerts/${id}`));
}

// status: "UnderReview" | "Resolved" | "Dismissed" (government officials only)
export function resolveAlert(id, status, note) {
  return unwrap(apiClient.post(`/ai/alerts/${id}/resolve`, { status, note }));
}

export function syncAlerts() {
  return unwrap(apiClient.post("/ai/alerts/sync"));
}
