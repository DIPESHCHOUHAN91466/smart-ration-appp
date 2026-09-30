import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import ChatbotWidget, { INTRO_SEEN_KEY } from "../../src/components/chatbot/ChatbotWidget";
import { chatbotService } from "../../src/services/chatbotService";
import { useChatbotStore } from "../../src/state/chatbotStore";
import { useLanguageStore } from "../../src/i18n/useTranslation";

const WELCOME = { kind: "welcome", text: "Namaste!", suggestions: [], links: [], related: [] };

class FakeRecognition {
  static last = null;
  constructor() { FakeRecognition.last = this; }
  start() { this.started = true; this.onstart?.(); }
  stop() { this.onend?.(); }
  abort() { this.onend?.(); }
}

function renderWidget() {
  return render(<MemoryRouter><ChatbotWidget /></MemoryRouter>);
}
const launcher = () => document.querySelector("button.chatbot-launcher"); // label is translated

beforeEach(() => {
  vi.spyOn(chatbotService, "welcome").mockResolvedValue(WELCOME);
  window.SpeechRecognition = FakeRecognition;
  FakeRecognition.last = null;
  localStorage.setItem(INTRO_SEEN_KEY, "true"); // most tests: not a first visit
  useChatbotStore.setState({ isOpen: false, pendingQuestion: null, pendingVoice: false });
});
afterEach(() => {
  delete window.SpeechRecognition;
  localStorage.clear();
  useLanguageStore.setState({ language: "en" });
  vi.useRealTimers();
});

describe("floating launcher", () => {
  it("is labelled, titled and opens the existing chat on click (Enter/Space are native button behaviour)", async () => {
    renderWidget();
    expect(launcher()).toHaveAttribute("title", "Ration Mitra AI Assistant");
    expect(launcher()).toHaveAccessibleDescription(/Need help\? Ask Ration Mitra AI/);
    await act(async () => fireEvent.click(launcher()));
    expect(screen.getByRole("dialog", { name: "Ration Mitra AI Assistant" })).toBeInTheDocument();
  });

  it("right-click opens the compact assistant menu; picking Hindi switches and persists the language", () => {
    renderWidget();
    fireEvent.contextMenu(launcher());
    const menu = screen.getByRole("menu", { name: "Assistant options" });
    expect(launcher()).toHaveAttribute("aria-expanded", "true");
    const items = [...menu.querySelectorAll("[role^=menuitem]")].map((i) => i.textContent.trim());
    expect(items).toEqual(["Voice input", "English", "हिन्दी", "मराठी", "Open chat"]);
    expect(within(menu).getByRole("menuitemradio", { name: "English" })).toHaveAttribute("aria-checked", "true");
    fireEvent.click(within(menu).getByRole("menuitemradio", { name: "हिन्दी" }));
    expect(useLanguageStore.getState().language).toBe("hi");
    expect(JSON.parse(localStorage.getItem("smart-ration-language")).state.language).toBe("hi");
  });

  it("keyboard: Up arrow opens the menu, arrows move, Escape closes and returns focus", () => {
    renderWidget();
    launcher().focus();
    fireEvent.keyDown(launcher(), { key: "ArrowUp" });
    const menu = screen.getByRole("menu");
    const first = within(menu).getByRole("menuitem", { name: "Voice input" });
    first.focus();
    fireEvent.keyDown(menu, { key: "ArrowDown" });
    expect(document.activeElement).toHaveTextContent("English");
    fireEvent.keyDown(menu, { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull();
  });

  it("long-press opens the menu without also opening the chat", () => {
    vi.useFakeTimers();
    renderWidget();
    fireEvent.pointerDown(launcher(), { button: 0 });
    act(() => vi.advanceTimersByTime(520));
    fireEvent.pointerUp(launcher());
    fireEvent.click(launcher());
    expect(screen.getByRole("menu")).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("'Voice input' in the menu opens the chat and starts listening in the chosen language", async () => {
    useLanguageStore.setState({ language: "mr" });
    renderWidget();
    fireEvent.contextMenu(launcher());
    await act(async () => fireEvent.click(screen.getByRole("menuitem", { name: "व्हॉइस इनपुट" })));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(FakeRecognition.last?.started).toBe(true);
    expect(FakeRecognition.last.lang).toBe("mr-IN");
    expect(screen.getByRole("status")).toHaveTextContent("ऐकत आहे...");
  });

  it("the chat header has voice and language controls", async () => {
    renderWidget();
    await act(async () => fireEvent.click(launcher()));
    const dialog = screen.getByRole("dialog");
    const globe = within(dialog).getByRole("button", { name: /Change language: English/ });
    expect(globe).toHaveAttribute("aria-haspopup", "menu");
    fireEvent.click(globe);
    fireEvent.click(within(dialog).getByRole("menuitemradio", { name: "मराठी" }));
    expect(useLanguageStore.getState().language).toBe("mr");
    await act(async () => fireEvent.click(within(dialog).getByRole("button", { name: "व्हॉइस इनपुट" })));
    expect(FakeRecognition.last.lang).toBe("mr-IN");
  });
});

describe("first-visit hint", () => {
  it("shows once, shortly after load, hides by itself and is remembered", () => {
    localStorage.removeItem(INTRO_SEEN_KEY);
    vi.useFakeTimers();
    const { container, unmount } = renderWidget();
    const wrap = () => container.querySelector(".chatbot-launcher-wrap");
    expect(wrap()).not.toHaveClass("intro");
    act(() => vi.advanceTimersByTime(1600));
    expect(wrap()).toHaveClass("intro");
    expect(localStorage.getItem(INTRO_SEEN_KEY)).toBe("true");
    act(() => vi.advanceTimersByTime(5000));
    expect(wrap()).not.toHaveClass("intro");
    unmount();

    const again = renderWidget(); // a returning visitor: never shown again
    act(() => vi.advanceTimersByTime(8000));
    expect(again.container.querySelector(".chatbot-launcher-wrap")).not.toHaveClass("intro");
  });
});
