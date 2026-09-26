import { describe, expect, it } from "vitest";
import { resolveApiBaseUrl, withApiVersion } from "../../src/services/apiBase";

describe("API base URL", () => {
  it("uses VITE_API_BASE_URL when set", () => {
    expect(resolveApiBaseUrl("https://api.example.org/api/v1", false)).toBe("https://api.example.org/api/v1");
  });

  it("adds the version to an older unversioned base", () => {
    expect(resolveApiBaseUrl("https://api.example.org/api", false)).toBe("https://api.example.org/api/v1");
    expect(withApiVersion("http://127.0.0.1:8000/api/")).toBe("http://127.0.0.1:8000/api/v1");
  });

  it("leaves a base that is not a bare /api alone", () => {
    expect(withApiVersion("https://gateway.example.org/ration")).toBe("https://gateway.example.org/ration");
  });

  it("falls back to the local API only in development", () => {
    expect(resolveApiBaseUrl("", true)).toBe("http://127.0.0.1:8000/api/v1");
  });

  it("never falls back to localhost in a production build", () => {
    expect(resolveApiBaseUrl("", false)).toBe("/api/v1");
  });
});
