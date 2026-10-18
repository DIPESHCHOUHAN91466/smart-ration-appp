import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import StaffApplicationSection from "../../src/pages/shared/StaffApplicationSection";
import StaffApplications from "../../src/pages/government/StaffApplications";
import * as staffService from "../../src/services/staffService";
import * as shopsService from "../../src/services/shopsService";
import { ToastProvider } from "../../src/state/ToastProvider";

const wrap = (ui) => render(<MemoryRouter><ToastProvider>{ui}</ToastProvider></MemoryRouter>);

function application(over = {}) {
  return {
    id: 7, userId: 3, applicantName: "Asha Patil", requestedRole: "ShopOwner", rationShopId: 3, rationShopName: "Third FPS",
    office: null, designation: "Dealer", proofReference: "LIC-778", status: "Pending", decisionReason: null, ...over,
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(shopsService, "getShops").mockResolvedValue([{ id: 3, shopName: "Third FPS" }]);
});

describe("Citizen: apply to work as a shop owner or official", () => {
  it("sends a shop-owner application with the chosen shop, then shows it as waiting and hides the form", async () => {
    const mine = vi.spyOn(staffService, "getMyStaffApplications").mockResolvedValueOnce([]).mockResolvedValue([application()]);
    const apply = vi.spyOn(staffService, "applyForStaffRole").mockResolvedValue(application());
    wrap(<StaffApplicationSection />);

    await screen.findByRole("option", { name: "Third FPS" });
    fireEvent.change(screen.getByLabelText("Ration shop"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Designation"), { target: { value: "Dealer" } });
    fireEvent.change(screen.getByLabelText("Licence or employee ID number"), { target: { value: "LIC-778" } });
    fireEvent.click(screen.getByRole("button", { name: "Send application" }));

    await waitFor(() => expect(apply).toHaveBeenCalledWith({
      requestedRole: "ShopOwner", rationShopId: 3, office: null, designation: "Dealer", proofReference: "LIC-778",
    }));
    expect(await screen.findByText("Pending")).toBeInTheDocument();
    expect(screen.queryByRole("form", { name: "Staff application" })).not.toBeInTheDocument();
    expect(mine).toHaveBeenCalledTimes(2);
  });

  it("lets the applicant withdraw a waiting application", async () => {
    vi.spyOn(staffService, "getMyStaffApplications").mockResolvedValue([application()]);
    const withdraw = vi.spyOn(staffService, "withdrawStaffApplication").mockResolvedValue(application({ status: "Withdrawn" }));
    wrap(<StaffApplicationSection />);

    fireEvent.click(await screen.findByRole("button", { name: "Withdraw" }));
    await waitFor(() => expect(withdraw).toHaveBeenCalledWith(7));
  });
});

describe("Admin: review staff applications", () => {
  it("never decides without a written reason, and sends the reason with the decision", async () => {
    vi.spyOn(staffService, "getStaffApplications").mockResolvedValue([application()]);
    const approve = vi.spyOn(staffService, "approveStaffApplication").mockResolvedValue(application({ status: "Approved" }));
    const reject = vi.spyOn(staffService, "rejectStaffApplication").mockResolvedValue(application({ status: "Rejected" }));
    wrap(<StaffApplications />);

    fireEvent.click(await screen.findByRole("button", { name: "Approve" }));
    expect(approve).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Reason for application 7"), { target: { value: "  Licence checked  " } });
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    await waitFor(() => expect(approve).toHaveBeenCalledWith(7, "Licence checked"));
    expect(reject).not.toHaveBeenCalled();
  });
});
