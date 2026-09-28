import apiClient, { unwrap } from "../api/client";

export function getProfile() {
  return unwrap(apiClient.get("/users/profile"));
}

export function updateProfile(payload) {
  return unwrap(apiClient.put("/users/profile", payload));
}
