import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import PublicLayout from "../../src/layouts/PublicLayout";
import LandingPage from "../../src/pages/landing/LandingPage";
import PublicHelpPage from "../../src/pages/public-help/PublicHelpPage";
import { publicHelpService } from "../../src/services/chatbotService";
import { useChatbotStore } from "../../src/state/chatbotStore";

vi.mock("../../src/components/QRCodeCanvas", () => ({ default: () => <canvas data-testid="qr" /> }));

const CATEGORIES = [
  { id: "how_to_apply", icon: "form", title: "How to Apply", description: "Applying for a ration card.", ask: "How can I apply for a ration card?", primaryArticle: "how_to_apply_card", quick: true, articles: [{ id: "how_to_apply_card", title: "How to apply for a ration card" }] },
  { id: "documents", icon: "file", title: "Required Documents", description: "Documents usually needed.", ask: "What documents are required?", primaryArticle: "required_documents", quick: true, articles: [{ id: "required_documents", title: "Documents usually required" }] },
];

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/help" element={<PublicHelpPage />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.spyOn(publicHelpService, "categories").mockResolvedValue(CATEGORIES);
  vi.spyOn(publicHelpService, "article").mockImplementation(async (id) => ({ kind: "answer", title: id === "required_documents" ? "Documents usually required" : "How to apply", text: "Steps:\n1. Visit the office\n2. Submit the form", links: [{ path: "/register", label: "Create account" }], related: [] }));
  vi.spyOn(publicHelpService, "search").mockResolvedValue([{ id: "required_documents", category: "documents", title: "Documents usually required", excerpt: "Commonly requested documents", score: 3 }]);
});

describe("landing page", () => {
  it("shows the hero, calls to action and main sections", () => {
    renderAt("/");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Your ration, on time");
    expect(screen.getAllByRole("link", { name: /get started/i })[0]).toHaveAttribute("href", "/register");
    expect(screen.getAllByRole("link", { name: /public help/i }).some((a) => a.getAttribute("href") === "/help")).toBe(true);
    for (const heading of ["How it works", "Services for everyone", "Why Smart Ration", "Contact & support"]) {
      expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
    }
    expect(screen.getByText(/Demonstration system/)).toBeInTheDocument();
  });

  it("has a skip link and a labelled language switcher", () => {
    renderAt("/");
    expect(screen.getByRole("link", { name: "Skip to main content" })).toHaveAttribute("href", "#main");
    expect(screen.getByRole("combobox", { name: "Language" })).toHaveValue("en");
  });

  it("switches the whole page to Marathi", async () => {
    const user = userEvent.setup();
    renderAt("/");
    await user.selectOptions(screen.getByRole("combobox", { name: "Language" }), "mr");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("तुमचे रेशन, वेळेवर");
    expect(document.documentElement.lang).toBe("mr");
  });

  it("loads FAQ answers from the help service on demand", async () => {
    const user = userEvent.setup();
    renderAt("/");
    const question = await screen.findByRole("button", { name: "What documents are required?" });
    await user.click(question);
    expect(question).toHaveAttribute("aria-expanded", "true");
    expect(publicHelpService.article).toHaveBeenCalledWith("required_documents", "en");
    expect(await screen.findByText("Visit the office")).toBeInTheDocument();
  });

  it("opens the assistant from the help section", async () => {
    const user = userEvent.setup();
    renderAt("/");
    await user.click(screen.getByRole("button", { name: /chat with the assistant/i }));
    expect(useChatbotStore.getState().isOpen).toBe(true);
  });
});

describe("Public Help page", () => {
  it("lists help categories and opens an article", async () => {
    const user = userEvent.setup();
    renderAt("/help");
    const card = await screen.findByRole("button", { name: /required documents/i });
    await user.click(card);
    await user.click(screen.getByRole("button", { name: /documents usually required/i }));
    const article = await screen.findByRole("heading", { level: 2, name: "Documents usually required" });
    expect(article).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create account/i })).toHaveAttribute("href", "/register");
    await user.click(screen.getByRole("button", { name: /all topics/i }));
    expect(await screen.findByRole("button", { name: /how to apply/i })).toBeInTheDocument();
  });

  it("searches help content", async () => {
    const user = userEvent.setup();
    renderAt("/help");
    await user.type(screen.getByRole("searchbox", { name: "Search help" }), "documents{Enter}");
    expect(publicHelpService.search).toHaveBeenCalledWith("documents", "en");
    const results = await screen.findByRole("list");
    expect(within(results).getByText("Documents usually required")).toBeInTheDocument();
  });

  it("offers the assistant when nothing matches", async () => {
    publicHelpService.search.mockResolvedValueOnce([]);
    const user = userEvent.setup();
    renderAt("/help");
    await user.type(screen.getByRole("searchbox", { name: "Search help" }), "weather{Enter}");
    await user.click(await screen.findByRole("button", { name: /ask the assistant/i }));
    expect(useChatbotStore.getState()).toMatchObject({ isOpen: true, pendingQuestion: "weather" });
  });

  it("shows an error with retry when help can't load", async () => {
    publicHelpService.categories.mockRejectedValueOnce(new Error("Network Error"));
    const user = userEvent.setup();
    renderAt("/help");
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Couldn't load help right now");
    await user.click(within(alert).getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("button", { name: /how to apply/i })).toBeInTheDocument();
  });
});
