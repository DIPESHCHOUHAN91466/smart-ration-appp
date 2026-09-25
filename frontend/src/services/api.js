import axios from "axios";
import { useAuthStore } from "../store/authStore";
import { API_BASE_URL } from "./apiBase";

// The Python backend: serves migrated routes itself and proxies the rest to the C# API.

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshInFlight = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;
    const isAuthRoute = originalRequest?.url?.includes("/auth/");

    if (status === 401 && originalRequest && !originalRequest._retry && !isAuthRoute) {
      originalRequest._retry = true;

      try {
        if (!refreshInFlight) {
          refreshInFlight = useAuthStore.getState().refreshAccessToken();
        }
        const newAccessToken = await refreshInFlight;
        refreshInFlight = null;

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        refreshInFlight = null;
        useAuthStore.getState().clearSession();
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          window.location.href = "/login";
        }
        return Promise.reject(normalizeError(refreshError));
      }
    }

    return Promise.reject(normalizeError(error));
  },
);

function normalizeError(error) {
  const data = error.response?.data;
  const message = data?.message || error.message || "Something went wrong. Please try again.";
  const normalized = new Error(message);
  normalized.status = error.response?.status;
  normalized.errors = data?.errors ?? null;
  return normalized;
}

// Unwraps the backend's { success, message, data } envelope into just `data`.
export function unwrap(axiosPromise) {
  return axiosPromise.then((response) => response.data?.data);
}

export default apiClient;
