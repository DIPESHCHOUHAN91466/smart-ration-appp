import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import MyVerification from "../../src/pages/rural/MyVerification";
import * as beneficiariesService from "../../src/services/beneficiariesService";

function profile(mobileStatus) {
  return {
    beneficiary: { id: 41 },
    aadhaarVerification: { status: "Verified", aadhaarMasked: "XXXX-XXXX-7173", verificationMode: "PRE_VERIFIED" },
    passbookVerification: { verificationStatus: "Verified", passbookNumber: "PB-DEMO-0001", status: "Active" },
    mobileVerification: { status: mobileStatus, mobileMasked: "******0077" },
    family: { members: [] },
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <MyVerification />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(beneficiariesService, "getEntitlement").mockResolvedValue(null);
});

describe("My Verification: mobile number", () => {
  it("explains how to verify a new number with a code when it is not verified", async () => {
    vi.spyOn(beneficiariesService, "getMyProfile").mockResolvedValue(profile("NotVerified"));
    renderPage();

    expect(await screen.findByRole("note")).toHaveTextContent("Sign in once with a code sent to the new number");
  });

  it("shows no hint when the number is verified", async () => {
    vi.spyOn(beneficiariesService, "getMyProfile").mockResolvedValue(profile("Verified"));
    renderPage();

    expect(await screen.findByText("******0077")).toBeInTheDocument();
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });
});
