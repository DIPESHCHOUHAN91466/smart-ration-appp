import { create } from "zustand";
import { persist } from "zustand/middleware";
import apiClient from "../api/client";

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      /** @param {import("../types/api").AuthResponse} authResponse */
      setSession: (authResponse) => {
        set({
          user: authResponse.user,
          accessToken: authResponse.accessToken,
          refreshToken: authResponse.refreshToken,
          isAuthenticated: true,
        });
      },

      clearSession: () => {
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
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
        const currentRefreshToken = get().refreshToken;
        if (!currentRefreshToken) {
          throw new Error("No refresh token available.");
        }

        const response = await apiClient.post("/auth/refresh", { refreshToken: currentRefreshToken });
        get().setSession(response.data.data);
        return response.data.data.accessToken;
      },

      logout: async () => {
        const refreshToken = get().refreshToken;
        get().clearSession();

        if (refreshToken) {
          try {
            await apiClient.post("/auth/logout", { refreshToken });
          } catch {
            // Best-effort — the local session is already cleared either way.
          }
        }
      },

      updateUser: (user) => set({ user }),
    }),
    {
      name: "smart-ration-auth",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
