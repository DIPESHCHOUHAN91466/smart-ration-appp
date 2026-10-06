import { describe, expect, it } from "vitest";
import { resolveApiBaseUrl, withApiVersion } from "../../src/api/baseUrl";

describe("API base URL", () => {
  it("uses VITE_API_BASE_URL when set", () => {
    expect(resolveApiBaseUrl("https://api.example.org/api/v1")).toBe("https://api.example.org/api/v1");
  });

  it("adds the version to an older unversioned base", () => {
    expect(resolveApiBaseUrl("https://api.example.org/api")).toBe("https://api.example.org/api/v1");
    expect(withApiVersion("http://127.0.0.1:8000/api/")).toBe("http://127.0.0.1:8000/api/v1");
  });

  it("leaves a base that is not a bare /api alone", () => {
    expect(withApiVersion("https://gateway.example.org/ration")).toBe("https://gateway.example.org/ration");
  });

  it("defaults to the same origin in development too (Vite proxies /api; the session cookie needs it)", () => {
    expect(resolveApiBaseUrl("")).toBe("/api/v1");
  });

  it("never falls back to localhost in a production build", () => {
    expect(resolveApiBaseUrl("")).toBe("/api/v1");
  });
});
