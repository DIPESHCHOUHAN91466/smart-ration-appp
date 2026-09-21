import apiClient, { unwrap } from "./api";

export function getNotifications() {
  return unwrap(apiClient.get("/notifications"));
}

export function markNotificationsRead(notificationIds) {
  return unwrap(apiClient.post("/notifications/read", { notificationIds }));
}
