import apiClient, { unwrap } from "./api";

export function getProfile() {
  return unwrap(apiClient.get("/users/profile"));
}

export function updateProfile(payload) {
  return unwrap(apiClient.put("/users/profile", payload));
}
