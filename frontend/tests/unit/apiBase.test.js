import { describe, expect, it } from "vitest";
import { resolveApiBaseUrl } from "../../src/services/apiBase";

describe("API base URL", () => {
  it("uses VITE_API_BASE_URL when set", () => {
    expect(resolveApiBaseUrl("https://api.example.org/api", false)).toBe("https://api.example.org/api");
  });

  it("falls back to the local API only in development", () => {
    expect(resolveApiBaseUrl("", true)).toBe("http://localhost:8000/api");
  });

  it("never falls back to localhost in a production build", () => {
    expect(resolveApiBaseUrl("", false)).toBe("/api");
  });
});
