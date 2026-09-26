import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ToastProvider } from "../../src/context/ToastContext";
import ProfileSection from "../../src/pages/shared/ProfileSection";
import * as usersService from "../../src/services/usersService";
import { useAuthStore } from "../../src/store/authStore";

const PROFILE = { id: 7, fullName: "Test Citizen", email: "citizen@example.org", mobileNumber: "9098000001", role: "RuralUser", rationShopId: null };

function renderSection() {
  return render(
    <ToastProvider>
      <ProfileSection />
    </ToastProvider>,
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
  useAuthStore.setState({ user: { id: 7, fullName: "Test Citizen", role: "RuralUser" } });
});

describe("My profile", () => {
  it("shows the profile with a read-only email and Save disabled until something changes", async () => {
    vi.spyOn(usersService, "getProfile").mockResolvedValue(PROFILE);
    renderSection();

    expect(await screen.findByDisplayValue("Test Citizen")).toBeInTheDocument();
    expect(screen.getByDisplayValue("citizen@example.org")).toHaveAttribute("readonly");
    expect(screen.getByDisplayValue("9098000001")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("saves trimmed values and updates the signed-in user's name", async () => {
    vi.spyOn(usersService, "getProfile").mockResolvedValue(PROFILE);
    const update = vi.spyOn(usersService, "updateProfile").mockImplementation(async (payload) => ({ ...PROFILE, ...payload }));
    renderSection();

    const name = await screen.findByDisplayValue("Test Citizen");
    await userEvent.clear(name);
    await userEvent.type(name, "  New Name  ");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(update).toHaveBeenCalledWith({ fullName: "New Name", mobileNumber: "9098000001" });
    expect(await screen.findByText("Profile saved")).toBeInTheDocument();
    expect(useAuthStore.getState().user.fullName).toBe("New Name");
  });

  it("shows the server's message when the mobile number is taken", async () => {
    vi.spyOn(usersService, "getProfile").mockResolvedValue(PROFILE);
    vi.spyOn(usersService, "updateProfile").mockRejectedValue(Object.assign(new Error("Another account already uses this mobile number."), { errors: [] }));
    renderSection();

    const mobile = await screen.findByDisplayValue("9098000001");
    await userEvent.clear(mobile);
    await userEvent.type(mobile, "9098000002");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect((await screen.findAllByText("Another account already uses this mobile number.")).length).toBeGreaterThan(0);
    expect(useAuthStore.getState().user.fullName).toBe("Test Citizen");
  });

  it("says so when the profile cannot be loaded", async () => {
    vi.spyOn(usersService, "getProfile").mockRejectedValue(new Error("offline"));
    renderSection();
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load your profile");
  });
});
