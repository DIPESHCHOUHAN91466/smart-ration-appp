import { afterEach, beforeEach, describe, expect, it } from "vitest";
import apiClient from "../../src/api/client";
import { useAuthStore } from "../../src/state/authStore";

// The real interceptors, with a fake network: every request is recorded and answered by `reply`.
let sent;
let reply;
const originalAdapter = apiClient.defaults.adapter;

function answer(config, status, data) {
  const response = { data, status, statusText: String(status), headers: {}, config };
  if (status >= 400) {
    const error = new Error(`status ${status}`);
    error.config = config;
    error.response = response;
    return Promise.reject(error);
  }
  return Promise.resolve(response);
}

beforeEach(() => {
  sent = [];
  apiClient.defaults.adapter = (config) => {
    sent.push({ url: config.url, auth: config.headers.Authorization ?? null });
    return reply(config);
  };
  window.history.replaceState(null, "", "/login");   // the redirect on a lost session stays put in tests
});

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter;
  useAuthStore.getState().clearSession();
});

const SESSION = { user: { id: 1, fullName: "Rahul", role: "RuralUser" }, accessToken: "fresh", refreshToken: null };

/** Signed in (as saved in localStorage) but, as after a page load, with no access token in memory. */
function afterPageLoad() {
  useAuthStore.setState({ user: SESSION.user, accessToken: null, isAuthenticated: true });
}

describe("API client sessions (HttpOnly refresh cookie, access token in memory)", () => {
  it("after a page load, gets a token from the cookie BEFORE the first call: no 401 and no repeated call", async () => {
    afterPageLoad();
    reply = (config) => (config.url === "/auth/refresh"
      ? answer(config, 200, { data: SESSION })
      : answer(config, config.headers.Authorization === "Bearer fresh" ? 200 : 401, { data: "ok" }));

    const response = await apiClient.get("/notifications");

    expect(response.status).toBe(200);
    expect(sent).toEqual([
      { url: "/auth/refresh", auth: null },
      { url: "/notifications", auth: "Bearer fresh" },
    ]);
  });

  it("calls made at the same time share one refresh", async () => {
    afterPageLoad();
    reply = (config) => answer(config, 200, { data: config.url === "/auth/refresh" ? SESSION : "ok" });

    await Promise.all([apiClient.get("/notifications"), apiClient.get("/ration/bookings"), apiClient.get("/shops")]);

    expect(sent.filter((r) => r.url === "/auth/refresh")).toHaveLength(1);
    expect(sent.filter((r) => r.url !== "/auth/refresh").every((r) => r.auth === "Bearer fresh")).toBe(true);
  });

  it("an expired cookie ends the session without calling the API", async () => {
    afterPageLoad();
    reply = (config) => answer(config, 401, { message: "Session expired" });

    await expect(apiClient.get("/notifications")).rejects.toThrow("Session expired");

    expect(sent.map((r) => r.url)).toEqual(["/auth/refresh"]);
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it("signed out: no refresh is attempted", async () => {
    useAuthStore.getState().clearSession();
    reply = (config) => answer(config, 200, { data: [] });

    await apiClient.get("/public-help/categories");

    expect(sent).toEqual([{ url: "/public-help/categories", auth: null }]);
  });

  it("a token that expires mid-session is still refreshed once and the call repeated", async () => {
    useAuthStore.setState({ user: SESSION.user, accessToken: "stale", isAuthenticated: true });
    reply = (config) => (config.url === "/auth/refresh"
      ? answer(config, 200, { data: SESSION })
      : answer(config, config.headers.Authorization === "Bearer fresh" ? 200 : 401, { data: "ok" }));

    const response = await apiClient.get("/notifications");

    expect(response.status).toBe(200);
    expect(sent.map((r) => [r.url, r.auth])).toEqual([
      ["/notifications", "Bearer stale"],
      ["/auth/refresh", "Bearer stale"],   // ignored by the API: the cookie is what refreshes
      ["/notifications", "Bearer fresh"],
    ]);
  });
});
