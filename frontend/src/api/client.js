import axios from "axios";
import { useAuthStore } from "../state/authStore";
import { API_BASE_URL } from "../config/env";

// The Python backend: serves migrated routes itself and proxies the rest to the C# API.

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // Cookie mode: the API keeps the refresh token in an HttpOnly cookie and never puts it in a response body.
  headers: { "Content-Type": "application/json", "X-Auth-Mode": "cookie" },
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
    // Sign-in, refresh and sign-out answer 401 for their own reasons; any other route (password change too)
    // may just need a fresh access token.
    const isAuthRoute = /\/auth\/(login|register|refresh|logout|otp|password\/reset)/.test(originalRequest?.url || "");

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

/** @returns {import("../types/api").ApiError} */
function normalizeError(error) {
  const data = error.response?.data;
  const message = data?.message || error.message || "Something went wrong. Please try again.";
  const normalized = new Error(message);
  normalized.status = error.response?.status;
  normalized.errors = data?.errors ?? null;
  return normalized;
}

/**
 * Unwraps the backend's { success, message, data } envelope into just `data`.
 * @template T
 * @param {Promise<import("axios").AxiosResponse<import("../types/api").ApiEnvelope<T>>>} axiosPromise
 * @returns {Promise<T | null>}
 */
export function unwrap(axiosPromise) {
  return axiosPromise.then((response) => response.data?.data);
}

export default apiClient;
