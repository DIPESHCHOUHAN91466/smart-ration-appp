import { describe, expect, it, vi } from "vitest";
import apiClient from "../../src/api/client";
import { useAuthStore } from "../../src/state/authStore";

// Security S7: no token is ever written to localStorage; the refresh token is an HttpOnly cookie the page can't read.
describe("auth session storage", () => {
  it("saves only the user summary, never a token", () => {
    useAuthStore.getState().setSession({
      user: { id: 1, fullName: "Rahul", role: "RuralUser" },
      accessToken: "header.payload.signature",
      refreshToken: null,
    });
    const saved = window.localStorage.getItem("smart-ration-auth");
    expect(saved).toContain("Rahul");
    expect(saved).not.toContain("header.payload.signature");
    expect(JSON.parse(saved).state).toEqual({ user: { id: 1, fullName: "Rahul", role: "RuralUser" }, isAuthenticated: true });
    expect(useAuthStore.getState().accessToken).toBe("header.payload.signature");   // in memory only
    useAuthStore.getState().clearSession();
  });

  it("starts no session when the password step asks for a two-factor code", async () => {
    useAuthStore.getState().clearSession();
    const post = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: { data: { mfaRequired: true, mfaToken: "pending", mfaExpiresInSeconds: 300 } },
    });
    const result = await useAuthStore.getState().login("officer@example.com", "pw");
    expect(result.mfaRequired).toBe(true);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    post.mockResolvedValueOnce({ data: { data: { user: { id: 3, role: "GovernmentOfficial" }, accessToken: "a", refreshToken: null } } });
    await useAuthStore.getState().verifyMfa("pending", "123456");
    expect(post).toHaveBeenLastCalledWith("/auth/mfa/verify", { mfaToken: "pending", code: "123456" });
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    useAuthStore.getState().clearSession();
  });

  it("asks the API for cookie mode on every request", () => {
    expect(apiClient.defaults.headers["X-Auth-Mode"]).toBe("cookie");
  });

  it("drops tokens saved by the previous version", async () => {
    window.localStorage.setItem("smart-ration-auth", JSON.stringify({
      state: { user: { id: 1 }, accessToken: "old-access", refreshToken: "old-refresh", isAuthenticated: true }, version: 0,
    }));
    await useAuthStore.persist.rehydrate();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(window.localStorage.getItem("smart-ration-auth")).not.toContain("old-refresh");
  });
});
