import { create } from "zustand";
import { persist } from "zustand/middleware";
import apiClient from "../api/client";

// Sessions (security S7): the refresh token is an HttpOnly cookie the page can never read (the API client sends
// X-Auth-Mode: cookie on every request). The access token lives in memory only: after a reload the first API call
// gets 401 and the client refreshes from the cookie. Only the user summary is saved in localStorage, for the UI.
export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,

      /** @param {import("../types/api").AuthResponse} authResponse */
      setSession: (authResponse) => {
        set({ user: authResponse.user, accessToken: authResponse.accessToken, isAuthenticated: true });
      },

      clearSession: () => {
        set({ user: null, accessToken: null, isAuthenticated: false });
      },

      login: async (email, password) => {
        const response = await apiClient.post("/auth/login", { email, password });
        get().setSession(response.data.data);
        return response.data.data;
      },

      register: async (payload) => {
        const response = await apiClient.post("/auth/register", payload);
        get().setSession(response.data.data);
        return response.data.data;
      },

      // Every other device is signed out by the backend; this one continues with the tokens it returns.
      changePassword: async (currentPassword, newPassword) => {
        const response = await apiClient.post("/auth/password/change", { currentPassword, newPassword });
        get().setSession(response.data.data);
        return response.data.data;
      },

      refreshAccessToken: async () => {
        const response = await apiClient.post("/auth/refresh", {});   // the cookie carries the refresh token
        get().setSession(response.data.data);
        return response.data.data.accessToken;
      },

      logout: async () => {
        get().clearSession();
        try {
          await apiClient.post("/auth/logout", {});   // revokes the session and removes the cookie
        } catch {
          // Best-effort — the local session is already cleared either way.
        }
      },

      updateUser: (user) => set({ user }),
    }),
    {
      name: "smart-ration-auth",
      version: 1,
      // Tokens are never written to storage. Version 0 kept both tokens here: drop them (one sign-in again).
      migrate: () => ({ user: null, isAuthenticated: false }),
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    },
  ),
);
