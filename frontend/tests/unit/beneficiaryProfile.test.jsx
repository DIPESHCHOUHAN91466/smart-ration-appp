import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import BeneficiaryProfile from "../../src/pages/shared/BeneficiaryProfile";
import * as beneficiariesService from "../../src/services/beneficiariesService";

// The shape of GET /api/beneficiaries/{id}/full-profile. For a citizen viewing their own profile the
// backend sends aiInsight: null and empty verification / QR-scan logs (staff-only information).
function fullProfile({ staff }) {
  return {
    profile: {
      id: 1, beneficiaryCode: "BEN-DEMO-0001", fullName: "Rahul Patil", gender: "Male", dateOfBirth: "1997-09-27",
      mobileMasked: "******0001", village: "Satnavari", district: "Nagpur", state: "Maharashtra", pincode: "441001",
      profilePhotoUrl: null, isActive: true, isBlocked: false, registrationDate: "2026-08-24",
      lastCollectionDate: null, nextCollectionDate: null,
    },
    family: { familyCode: "FAM-DEMO-0001", familyHeadName: "Rahul Patil", familySize: 1, eligibleMemberCount: 1,
      members: [{ id: 1, fullName: "Rahul Patil", age: 29, relationship: "Head", eligibility: "Eligible" }] },
    rationCard: { rationCardNumber: "PB-DEMO-0001", status: "ACTIVE", schemeCode: "DEMO-NFSA", schemeName: "Demo", familySize: 1 },
    aadhaarVerification: { status: "Verified", aadhaarMasked: "XXXX-XXXX-7173", verificationDate: "2026-08-24",
      verificationSource: "SYNTHETIC_DEMO", verificationMode: "PRE_VERIFIED" },
    passbookVerification: { passbookNumber: "PB-DEMO-0001", status: "ACTIVE", verificationStatus: "Verified",
      lastUpdated: "2026-09-23", verificationSource: "SYNTHETIC_DEMO" },
    mobileVerification: { mobileMasked: "******0001", status: "Verified", verifiedAt: "2026-08-24 02:34" },
    entitlement: { schemeCode: "DEMO-NFSA", schemeName: "Demo", familySize: 1, eligibleMemberCount: 1,
      items: [{ rationType: "Rice", monthlyEntitlement: 5, alreadyCollected: 0, remaining: 5, todayAllocation: 5 }] },
    currentQr: null,
    collectionHistory: [],
    verificationHistory: staff
      ? [{ id: 9, verificationReference: null, tokenNumber: "SR-2026-000001", beneficiaryId: 1, shopId: 1,
          action: "BeneficiaryVerified", verificationMethod: "QR", status: "SUCCESS", reason: null, operatorId: 2,
          timestamp: "2026-09-29 11:10:43" }]
      : [],
    qrScanHistory: [],
    aiInsight: staff ? { riskLevel: "High", reasons: ["3 open anomaly alert(s) on record"], explanation: "Review first." } : null,
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/beneficiary/1"]}>
      <Routes>
        <Route path="/beneficiary/:id" element={<BeneficiaryProfile />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => vi.restoreAllMocks());

describe("Beneficiary profile", () => {
  it("never shows AI risk or audit logs to the citizen themself", async () => {
    vi.spyOn(beneficiariesService, "getFullProfile").mockResolvedValue(fullProfile({ staff: false }));
    renderPage();

    expect((await screen.findAllByText("Rahul Patil")).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "AI Insights & Audit" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "QR & Collection History" }));
    expect(screen.queryByText("QR SCAN HISTORY")).not.toBeInTheDocument();
    expect(screen.queryByText(/Risk/)).not.toBeInTheDocument();
  });

  it("still shows them to staff", async () => {
    vi.spyOn(beneficiariesService, "getFullProfile").mockResolvedValue(fullProfile({ staff: true }));
    renderPage();

    await userEvent.click(await screen.findByRole("button", { name: "AI Insights & Audit" }));
    expect(screen.getByText("High Risk")).toBeInTheDocument();
    expect(screen.getByText("3 open anomaly alert(s) on record")).toBeInTheDocument();
  });
});
