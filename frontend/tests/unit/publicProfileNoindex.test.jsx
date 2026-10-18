import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import PublicProfile from "../../src/pages/PublicProfile";
import * as publicService from "../../src/services/publicService";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Public verification badge", () => {
  it("asks search engines not to index it, and removes that request when the page closes", async () => {
    vi.spyOn(publicService, "getPublicBeneficiaryProfile").mockRejectedValue(new Error("Profile not found."));
    const view = render(
      <MemoryRouter initialEntries={["/profile/SRB-TEST"]}>
        <Routes>
          <Route path="/profile/:publicReference" element={<PublicProfile />} />
        </Routes>
      </MemoryRouter>,
    );
    await screen.findByText("Profile not found.");
    expect(document.head.querySelector('meta[name="robots"]')?.getAttribute("content")).toBe("noindex, nofollow");

    view.unmount();
    expect(document.head.querySelector('meta[name="robots"]')).toBeNull();
  });
});
