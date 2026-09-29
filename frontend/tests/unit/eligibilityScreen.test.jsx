import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import QrScanResult from "../../src/components/qr/QrScanResult";
import { displayAadhaar, familyCounts, initials, unitTotals } from "../../src/features/qr/familyEligibility";
import { useLanguageStore } from "../../src/i18n/useTranslation";

// The verification object in the shape POST /api/qr/scan returns (synthetic test values).
function member(i, overrides = {}) {
  return {
    id: i, fullName: `Member ${i}`, age: 20 + i, relationship: i === 1 ? "Head" : "Son", eligibility: "Eligible",
    isHead: i === 1, gender: i === 1 ? "Male" : "Male", aadhaarMasked: i === 1 ? "XXXX-XXXX-1234" : null,
    identityVerified: i === 1 ? true : null, photoUrl: null,
    monthlyEntitlement: [{ rationType: "Rice", quantity: 5 }, { rationType: "Wheat", quantity: 3 }], ...overrides,
  };
}

function verification({ members = [member(1)], passbookNumber = "PB-DEMO-0001", summary = {} } = {}) {
  return {
    beneficiary: { id: 1, fullName: "Member 1", mobileMasked: "******0001" },
    family: { familyCode: "FAM-DEMO-0001", familySize: members.length, eligibleMemberCount: members.filter((m) => m.eligibility === "Eligible").length, members },
    aadhaarVerification: { aadhaarMasked: "XXXX-XXXX-1234", status: "Verified" },
    passbookVerification: passbookNumber ? { passbookNumber, verificationStatus: "Verified" } : null,
    booking: { tokenId: 7, tokenNumber: "SR-2026-010104", status: "Confirmed", collectionDate: "2026-09-29", bookingTime: "12:00", shopName: "Satnavari Ration Shop" },
    entitlement: {
      schemeCode: "DEMO-NFSA", eligibleMemberCount: members.length,
      items: [
        { rationType: "Rice", todayAllocation: 5 }, { rationType: "Wheat", todayAllocation: 3 }, { rationType: "Sugar", todayAllocation: 1 },
        { rationType: "Pulses", todayAllocation: 1 }, { rationType: "EdibleOil", todayAllocation: 0.5 }, { rationType: "Salt", todayAllocation: 0.25 },
      ],
    },
    verificationSummary: { aadhaarVerified: true, passbookVerified: true, mobileVerified: true, tokenValid: true, familyEligible: true, entitlementAvailable: true, overallStatus: "READY_FOR_RATION_COLLECTION", ...summary },
  };
}

function renderResult(result, handlers = {}) {
  const props = { onContinue: vi.fn(), onScanAgain: vi.fn(), onManual: vi.fn(), onRetry: vi.fn(), ...handlers };
  render(<QrScanResult result={result} {...props} />);
  return props;
}

afterEach(() => useLanguageStore.setState({ language: "en" }));

describe("family eligibility helpers", () => {
  it("counts eligible members dynamically", () => {
    expect(familyCounts({ members: [member(1), member(2), member(3, { eligibility: "NotEligible" })] })).toEqual({ total: 3, eligible: 2, allEligible: false });
    expect(familyCounts({ members: [member(1)] }).allEligible).toBe(true);
    expect(familyCounts({ members: [] }).total).toBe(0);
  });

  it("totals kilograms and litres separately", () => {
    expect(unitTotals(verification().entitlement.items, "todayAllocation")).toEqual({ kg: 10.25, L: 0.5 });
  });

  it("only ever displays a masked Aadhaar", () => {
    expect(displayAadhaar("XXXX-XXXX-1234")).toBe("XXXX XXXX 1234");
    expect(displayAadhaar("123412341234")).toBeNull(); // a full number is refused, not shown
    expect(displayAadhaar(null)).toBeNull();
    expect(initials("Rahul Patil")).toBe("RP");
  });
});

describe("QrScanResult — eligible for collection", () => {
  it("shows token, customer, ration card, dynamic family count, steps and entitlement", () => {
    const members = [1, 2, 3, 4, 5].map((i) => member(i));
    const handlers = renderResult({ status: "VERIFIED", verification: verification({ members }) });
    expect(screen.getByText("Customer Verified")).toBeInTheDocument();
    expect(screen.getByText("SR-2026-010104")).toBeInTheDocument();
    expect(screen.getAllByText("PB-DEMO-0001").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/5 Members · All Eligible/).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("listitem").filter((li) => li.className.includes("member-card"))).toHaveLength(5);
    expect(screen.getByText("XXXX XXXX 1234")).toBeInTheDocument();
    expect(screen.getByText("10.25 kg")).toBeInTheDocument(); // dry goods
    expect(screen.getByText("0.5 L")).toBeInTheDocument();    // liquids, not added to kg
    fireEvent.click(screen.getByRole("button", { name: /Continue Distribution/ }));
    expect(handlers.onContinue).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: /Scan Another QR/ }));
    expect(handlers.onScanAgain).toHaveBeenCalledTimes(1);
  });

  it("handles 1 and 10 members, and mixed eligibility", () => {
    const ten = Array.from({ length: 10 }, (_, i) => member(i + 1, i >= 7 ? { eligibility: "NotEligible", monthlyEntitlement: [] } : {}));
    renderResult({ status: "VERIFIED", verification: verification({ members: ten }) });
    expect(screen.getAllByText("7 / 10 Members Eligible").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Not Eligible").length).toBeGreaterThanOrEqual(3);
  });

  it("never invents missing data: no photo -> initials, no Aadhaar / ration card -> Not recorded", () => {
    renderResult({ status: "VERIFIED", verification: verification({ members: [member(1), member(2)], passbookNumber: null }) });
    expect(screen.getByRole("img", { name: "Photo of Member 2" })).toHaveTextContent("M2");
    expect(screen.getAllByText("Not recorded").length).toBeGreaterThanOrEqual(2);
  });

  it("falls back to initials when a stored photo fails to load", () => {
    renderResult({ status: "VERIFIED", verification: verification({ members: [member(1, { photoUrl: "/broken.jpg" })] }) });
    const img = screen.getByRole("img", { name: "Photo of Member 1" });
    fireEvent.error(img);
    expect(screen.getByRole("img", { name: "Photo of Member 1" })).toHaveTextContent("M1");
  });

  it("expands member details with the monthly entitlement share", () => {
    renderResult({ status: "VERIFIED", verification: verification() });
    const toggle = screen.getByRole("button", { name: /View Details/ });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    const details = document.getElementById(toggle.getAttribute("aria-controls"));
    expect(within(details).getByText("Monthly entitlement share")).toBeInTheDocument();
    expect(within(details).getByText("5 kg")).toBeInTheDocument();
  });

  it("an empty family does not break the page and offers a retry", () => {
    const handlers = renderResult({ status: "VERIFIED", verification: verification({ members: [] }) });
    expect(screen.getByText("No family member records available.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Retry Verification/ }));
    expect(handlers.onRetry).toHaveBeenCalled();
  });
});

describe("QrScanResult — other outcomes", () => {
  it("already collected: warning, no Continue Distribution, entitlement hidden", () => {
    renderResult({ status: "ALREADY_COLLECTED", verification: verification({ summary: { overallStatus: "COLLECTION_BLOCKED" } }) });
    expect(screen.getByText("Token Already Used")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Continue Distribution/ })).toBeNull();
    expect(screen.queryByText("Ration Entitlement")).toBeNull();
    expect(screen.getAllByText("Distribution blocked").length).toBeGreaterThan(0);
  });

  it("invalid QR and network error show clear actions", () => {
    const { onRetry } = renderResult({ status: "NETWORK_ERROR" });
    fireEvent.click(screen.getByRole("button", { name: /Try Again/i }));
    expect(onRetry).toHaveBeenCalled();
  });

  it("renders in Hindi and Marathi", () => {
    useLanguageStore.setState({ language: "hi" });
    const { unmount } = render(<QrScanResult result={{ status: "VERIFIED", verification: verification() }} onContinue={() => {}} onScanAgain={() => {}} onManual={() => {}} onRetry={() => {}} />);
    expect(screen.getByText("ग्राहक सत्यापित")).toBeInTheDocument();
    expect(screen.getAllByText(/परिवार का मुखिया/).length).toBeGreaterThan(0);
    unmount();
    useLanguageStore.setState({ language: "mr" });
    render(<QrScanResult result={{ status: "VERIFIED", verification: verification() }} onContinue={() => {}} onScanAgain={() => {}} onManual={() => {}} onRetry={() => {}} />);
    expect(screen.getAllByText(/कुटुंब प्रमुख/).length).toBeGreaterThan(0);
    expect(screen.getByText("वितरणासाठी पात्र कुटुंब सदस्य")).toBeInTheDocument();
  });
});
