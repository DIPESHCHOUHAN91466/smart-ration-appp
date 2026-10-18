import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Bookings, { PAGE_LIMIT } from "../../src/pages/government/Bookings";
import * as rationService from "../../src/services/rationService";

function booking(id) {
  return {
    id, tokenNumber: `SR-2026-${String(id).padStart(6, "0")}`, userName: `Citizen ${id}`, rationShopName: "Satnavari FPS",
    slotDate: "2026-10-18T00:00:00", startTime: "09:00:00", status: "Confirmed", createdAt: "2026-10-18T03:00:00",
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <Bookings />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Official bookings page: filtered and paged on the server", () => {
  it("asks for the newest page only, never the whole list", async () => {
    const spy = vi.spyOn(rationService, "getBookings").mockResolvedValue([booking(2), booking(1)]);
    renderPage();

    expect(await screen.findByText("SR-2026-000002")).toBeInTheDocument();
    expect(spy).toHaveBeenCalledWith({ limit: PAGE_LIMIT });
    expect(screen.getByText("2 booking(s)")).toBeInTheDocument();
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });

  it("sends the status and the search to the server", async () => {
    const spy = vi.spyOn(rationService, "getBookings").mockResolvedValue([booking(1)]);
    renderPage();
    await screen.findByText("SR-2026-000001");

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Cancelled" } });
    await waitFor(() => expect(spy).toHaveBeenLastCalledWith({ limit: PAGE_LIMIT, status: "Cancelled" }));

    fireEvent.change(screen.getByPlaceholderText("Search token, user, shop..."), { target: { value: "  ravi " } });
    await waitFor(() => expect(spy).toHaveBeenLastCalledWith({ limit: PAGE_LIMIT, status: "Cancelled", q: "ravi" }));
  });

  it("says when only the newest page is shown", async () => {
    vi.spyOn(rationService, "getBookings").mockResolvedValue(Array.from({ length: PAGE_LIMIT }, (_, i) => booking(i + 1)));
    renderPage();

    expect(await screen.findByRole("note")).toHaveTextContent(`Showing the newest ${PAGE_LIMIT}`);
    expect(screen.getByText(`Newest ${PAGE_LIMIT} booking(s)`)).toBeInTheDocument();
  });

  it("tells an empty search apart from no bookings at all", async () => {
    vi.spyOn(rationService, "getBookings").mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText("No bookings yet")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("Search token, user, shop..."), { target: { value: "nobody" } });
    expect(await screen.findByText("No matching bookings")).toBeInTheDocument();
  });
});
