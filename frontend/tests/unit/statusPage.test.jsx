import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import StatusPage from "../../src/pages/status/StatusPage";

const HEALTH = { status: "healthy", database: "healthy", legacyApi: "healthy", aiService: "unhealthy", chatbot: "healthy", dataMode: "synthetic" };
const READY = { ready: true, checks: { database: "ok", migrations: "ok", legacyApi: "ok" } };

describe("developer status page", () => {
  it("shows every component's state from /health, /ready and the C# health endpoint", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url) => ({
      status: 200,
      json: async () => (url.endsWith("/ready") ? READY : url.endsWith("/api/health") ? { success: true } : HEALTH),
    })));
    render(<StatusPage />);
    const table = await screen.findByRole("table");
    const row = (name) => within(table).getByRole("row", { name: new RegExp(name) });
    expect(row("MySQL database")).toHaveTextContent("healthy");
    expect(row("AI service")).toHaveTextContent("unhealthy");
    expect(row("Data mode")).toHaveTextContent("synthetic");
    expect(row("Data mode")).toHaveTextContent("demo data — not real citizens");
    expect(row("Ready for traffic")).toHaveTextContent("ok");
    vi.unstubAllGlobals();
  });

  it("marks the API unreachable when the request fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
    render(<StatusPage />);
    const table = await screen.findByRole("table");
    expect(within(table).getByRole("row", { name: /^Python API/ })).toHaveTextContent("unreachable");
    vi.unstubAllGlobals();
  });
});
