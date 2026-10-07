import axios from "axios";
import { useAuthStore } from "../state/authStore";
import { API_BASE_URL } from "../config/env";

// The Python backend: serves migrated routes itself and proxies the rest to the C# API.

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // Cookie mode: the API keeps the refresh token in an HttpOnly cookie and never puts it in a response body.
  headers: { "Content-Type": "application/json", "X-Auth-Mode": "cookie" },
});

// Sign-in, refresh and sign-out answer 401 for their own reasons and never need an access token first.
const AUTH_ROUTE = /\/auth\/(login|register|refresh|logout|otp|password\/reset|mfa\/verify)/;

// One refresh at a time: every request that needs a token while it runs waits for the same answer.
let refreshInFlight = null;
function refreshOnce() {
  if (!refreshInFlight) {
    refreshInFlight = useAuthStore.getState().refreshAccessToken().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

function endSession() {
  useAuthStore.getState().clearSession();
  if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    window.location.href = "/login";
  }
}

apiClient.interceptors.request.use(async (config) => {
  const { accessToken, isAuthenticated } = useAuthStore.getState();
  let token = accessToken;
  // After a page load the access token (memory only) is gone but the session cookie is not: get a new token
  // BEFORE the first call, instead of letting every call fail with 401 and repeat it.
  if (!token && isAuthenticated && !AUTH_ROUTE.test(config.url || "")) {
    try {
      token = await refreshOnce();
    } catch (refreshError) {
      endSession();
      throw normalizeError(refreshError);
    }
  }
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;
    // Any other route (password change too) may just need a fresh access token, e.g. one expired mid-session.
    const isAuthRoute = AUTH_ROUTE.test(originalRequest?.url || "");

    if (status === 401 && originalRequest && !originalRequest._retry && !isAuthRoute) {
      originalRequest._retry = true;

      try {
        const newAccessToken = await refreshOnce();
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        endSession();
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
  normalized.errorCode = data?.errorCode ?? null;
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
