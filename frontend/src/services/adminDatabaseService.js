import apiClient, { unwrap } from "../api/client";

export function getDatabaseTables() {
  return unwrap(apiClient.get("/admin/database/tables"));
}

export function getDatabaseTableRows(table, params) {
  return unwrap(apiClient.get(`/admin/database/${table}`, { params }));
}
