// Screen readers must hear toasts (WCAG 4.1.3 status messages): the live region exists before any message,
// errors are alerts (announced at once), other messages are polite status updates.
import { act, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ToastProvider } from "../../src/state/ToastProvider";
import { useToast } from "../../src/state/toast";

let notify;
function Grab() {
  notify = useToast();
  return null;
}

describe("toast announcements", () => {
  it("keeps a polite live region in the page before any toast", () => {
    const { container } = render(<ToastProvider><Grab /></ToastProvider>);
    const region = container.querySelector(".toast-region");
    expect(region).not.toBeNull();
    expect(region.getAttribute("aria-live")).toBe("polite");
    expect(region.textContent).toBe("");
  });

  it("announces errors as alerts and other messages as status", () => {
    render(<ToastProvider><Grab /></ToastProvider>);
    act(() => notify("Could not load the dashboard.", "error"));
    expect(screen.getByRole("alert")).toHaveTextContent("Could not load the dashboard.");
    act(() => notify("Booking confirmed"));
    expect(screen.getByRole("status")).toHaveTextContent("Booking confirmed");
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
