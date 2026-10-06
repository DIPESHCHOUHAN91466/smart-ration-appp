import { describe, expect, it } from "vitest";
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
