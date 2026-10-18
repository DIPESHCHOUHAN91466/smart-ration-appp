import apiClient, { unwrap } from "../api/client";

// Staff onboarding (migration 0009): a citizen applies to work as a shop owner or official; only an Admin decides.

export function applyForStaffRole(payload) {
  return unwrap(apiClient.post("/staff-applications", payload));
}

export function getMyStaffApplications() {
  return unwrap(apiClient.get("/staff-applications/mine"));
}

export function withdrawStaffApplication(id) {
  return unwrap(apiClient.post(`/staff-applications/${id}/withdraw`));
}

export function getStaffApplications(status = "Pending") {
  return unwrap(apiClient.get("/admin/staff-applications", { params: { status, limit: 200 } }));
}

export function approveStaffApplication(id, reason) {
  return unwrap(apiClient.post(`/admin/staff-applications/${id}/approve`, { reason }));
}

export function rejectStaffApplication(id, reason) {
  return unwrap(apiClient.post(`/admin/staff-applications/${id}/reject`, { reason }));
}
