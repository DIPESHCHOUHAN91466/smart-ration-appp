import apiClient, { unwrap } from "../api/client";

export function getGovernmentDashboard() {
  return unwrap(apiClient.get("/admin/dashboard"));
}

export function getStatistics(fromDate, toDate) {
  const params = {};
  if (fromDate) params.fromDate = fromDate;
  if (toDate) params.toDate = toDate;
  return unwrap(apiClient.get("/admin/statistics", { params }));
}

export function getReports(fromDate, toDate) {
  const params = {};
  if (fromDate) params.fromDate = fromDate;
  if (toDate) params.toDate = toDate;
  return unwrap(apiClient.get("/admin/reports", { params }));
}

export function getUsers(role) {
  return unwrap(apiClient.get("/admin/users", { params: role ? { role } : {} }));
}
