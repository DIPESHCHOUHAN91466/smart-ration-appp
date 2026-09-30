import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import ChatbotWidget from "../../src/components/chatbot/ChatbotWidget";
import { chatbotService } from "../../src/services/chatbotService";
import { openChatbot } from "../../src/state/chatbotStore";
import { useLanguageStore } from "../../src/i18n/useTranslation";

const SUGGESTIONS = [
  { topic: "documents", label: "Required Documents", ask: "What documents are required?" },
  { topic: "token_slots", label: "Token & Slots", ask: "How do I book a time slot and get a token?" },
];
const WELCOME = { kind: "welcome", text: "Namaste! 👋\nI'm the Ration Mitra AI Assistant.\n• Ration cards\n• Eligibility", suggestions: SUGGESTIONS, links: [], related: [] };
const answer = (text, extra = {}) => ({ kind: "answer", title: "Documents usually required", text, links: [], related: [], suggestions: SUGGESTIONS, ...extra });

function renderWidget(path = "/") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <ChatbotWidget />
    </MemoryRouter>,
  );
}

async function openWidget(user) {
  await user.click(screen.getByRole("button", { name: /open ration mitra ai assistant/i }));
  return screen.findByRole("dialog", { name: "Ration Mitra AI Assistant" });
}

beforeEach(() => {
  vi.spyOn(chatbotService, "welcome").mockResolvedValue(WELCOME);
  vi.spyOn(chatbotService, "send").mockResolvedValue(answer("Commonly requested documents:\n• Identity proof\n• Proof of address"));
});

describe("Public Help chatbot", () => {
  it("shows a floating launcher with an unread indicator and tooltip", () => {
    renderWidget();
    const launcher = screen.getByRole("button", { name: /open ration mitra ai assistant \(1 unread message\)/i });
    expect(launcher).toHaveClass("has-unread");
    expect(screen.getByRole("tooltip")).toHaveTextContent("Need help? Ask Ration Mitra AI");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("opens with the welcome message and quick questions, then clears the unread badge", async () => {
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    expect(await within(dialog).findByText("I'm the Ration Mitra AI Assistant.")).toBeInTheDocument();
    expect(within(dialog).getByText("Ration cards").tagName).toBe("LI");            // bullet lines become a list
    expect(within(dialog).getByRole("group", { name: "Quick questions" })).toBeInTheDocument();
    expect(chatbotService.welcome).toHaveBeenCalledWith("en");
    await waitFor(() => expect(within(dialog).getByRole("textbox", { name: "Ask anything about Smart Ration..." })).toHaveFocus());
  });

  it("asks a quick question by topic and shows the answer", async () => {
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    await user.click(await within(dialog).findByRole("button", { name: "Required Documents" }));
    expect(chatbotService.send).toHaveBeenCalledWith({ topic: "documents", language: "en" });
    expect(within(dialog).getByText("What documents are required?")).toBeInTheDocument();   // shown as the user's message
    expect(await within(dialog).findByText("Proof of address")).toBeInTheDocument();
  });

  it("sends a typed message with Enter in the current language", async () => {
    useLanguageStore.setState({ language: "hi" });
    const user = userEvent.setup();
    renderWidget();
    await user.click(screen.getByRole("button", { name: /राशन मित्र AI सहायक खोलें/ }));
    const input = await screen.findByRole("textbox", { name: "स्मार्ट राशन के बारे में कुछ भी पूछें..." });
    await user.type(input, "राशन कार्ड कैसे बनवाएं{Enter}");
    expect(chatbotService.send).toHaveBeenCalledWith({ message: "राशन कार्ड कैसे बनवाएं", language: "hi" });
    expect(input).toHaveValue("");
  });

  it("does not send empty messages", async () => {
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    const send = within(dialog).getByRole("button", { name: "Send message" });
    expect(send).toBeDisabled();
    await user.type(within(dialog).getByRole("textbox"), "   {Enter}");
    expect(chatbotService.send).not.toHaveBeenCalled();
  });

  it("shows a friendly error with retry when the service is unreachable", async () => {
    chatbotService.send.mockRejectedValueOnce(Object.assign(new Error("Network Error"), { status: undefined }));
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    await user.type(within(dialog).getByRole("textbox"), "documents{Enter}");
    const alert = await within(dialog).findByRole("alert");
    expect(alert).toHaveTextContent("couldn't reach the help service");
    await user.click(within(alert).getByRole("button", { name: "Retry" }));
    expect(await within(dialog).findByText("Proof of address")).toBeInTheDocument();
    expect(within(dialog).queryByRole("alert")).not.toBeInTheDocument();
    expect(chatbotService.send).toHaveBeenCalledTimes(2);
  });

  it("explains rate limiting", async () => {
    chatbotService.send.mockRejectedValueOnce(Object.assign(new Error("Too many"), { status: 429 }));
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    await user.type(within(dialog).getByRole("textbox"), "hello{Enter}");
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("sending messages quickly");
  });

  it("renders replies as text only: no markup, no external links", async () => {
    chatbotService.send.mockResolvedValueOnce(answer("<script>alert(1)</script> <img src=x onerror=alert(2)>", {
      links: [{ path: "/login", label: "Log in securely" }, { path: "https://evil.example.com", label: "Evil" }, { path: "//evil.example.com", label: "Evil2" }],
    }));
    const user = userEvent.setup();
    const { container } = renderWidget();
    const dialog = await openWidget(user);
    await user.type(within(dialog).getByRole("textbox"), "test{Enter}");
    expect(await within(dialog).findByText(/<script>alert\(1\)<\/script>/)).toBeInTheDocument(); // shown literally
    expect(container.querySelector("script, img[src='x']")).toBeNull();
    expect(within(dialog).getByRole("link", { name: /log in securely/i })).toHaveAttribute("href", "/login");
    expect(within(dialog).queryByRole("link", { name: /evil/i })).not.toBeInTheDocument();
  });

  it("marks private-data answers and offers a secure login link", async () => {
    chatbotService.send.mockResolvedValueOnce({
      kind: "private_data", text: "For your personal details … please log in securely.", requiresLogin: true,
      links: [{ path: "/login", label: "Log in securely" }], related: [], suggestions: SUGGESTIONS,
    });
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    await user.type(within(dialog).getByRole("textbox"), "What is my token?{Enter}");
    const bubble = (await within(dialog).findByText(/please log in securely/)).closest(".chat-bubble");
    expect(bubble).toHaveClass("kind-private_data");
    expect(within(bubble).getByRole("link", { name: /log in securely/i })).toBeInTheDocument();
  });

  it("opens a related topic by article id", async () => {
    chatbotService.send
      .mockResolvedValueOnce(answer("Apply at the supply office.", { related: [{ id: "required_documents", title: "Documents usually required" }] }))
      .mockResolvedValueOnce(answer("Identity proof…"));
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    await user.type(within(dialog).getByRole("textbox"), "apply{Enter}");
    await user.click(await within(dialog).findByRole("button", { name: "Documents usually required" }));
    expect(chatbotService.send).toHaveBeenLastCalledWith({ articleId: "required_documents", language: "en" });
  });

  it("closes with Escape and returns focus to the launcher; history is kept", async () => {
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    await user.type(within(dialog).getByRole("textbox"), "documents{Enter}");
    await within(dialog).findByText("Proof of address");
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: /open ration mitra ai assistant/i })).toHaveFocus());
    expect(JSON.parse(sessionStorage.getItem("smart-ration-chat")).map((m) => m.role)).toEqual(["bot", "user", "bot"]);
    await openWidget(user);
    expect(screen.getByText("Proof of address")).toBeInTheDocument();                      // conversation restored
  });

  it("minimize and close buttons both hide the window", async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole("button", { name: "Minimize assistant" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await openWidget(user);
    await user.click(screen.getByRole("button", { name: "Close assistant" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("expands and restores the window", async () => {
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    await user.click(within(dialog).getByRole("button", { name: "Expand" }));
    expect(dialog).toHaveClass("expanded");
    await user.click(within(dialog).getByRole("button", { name: "Restore size" }));
    expect(dialog).not.toHaveClass("expanded");
  });

  it("clears the conversation and starts again with the welcome", async () => {
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    await user.type(within(dialog).getByRole("textbox"), "documents{Enter}");
    await within(dialog).findByText("Proof of address");
    await user.click(within(dialog).getByRole("button", { name: "Clear conversation" }));
    await waitFor(() => expect(within(dialog).queryByText("Proof of address")).not.toBeInTheDocument());
    expect(await within(dialog).findByText("I'm the Ration Mitra AI Assistant.")).toBeInTheDocument();
  });

  it("searches within the conversation", async () => {
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    await user.type(within(dialog).getByRole("textbox"), "documents{Enter}");
    await within(dialog).findByText("Proof of address");
    await user.click(within(dialog).getByRole("button", { name: "Search conversation" }));
    await user.type(within(dialog).getByRole("searchbox"), "address");
    expect(within(dialog).queryByText("I'm the Ration Mitra AI Assistant.")).not.toBeInTheDocument();
    expect(within(dialog).getByText("Proof of address")).toBeInTheDocument();
    await user.clear(within(dialog).getByRole("searchbox"));
    await user.type(within(dialog).getByRole("searchbox"), "zzz");
    expect(within(dialog).getByText("No messages match your search.")).toBeInTheDocument();
  });

  it("can be opened from any page with a question", async () => {
    renderWidget();
    openChatbot("What documents are required?");
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    await waitFor(() => expect(chatbotService.send).toHaveBeenCalledWith({ message: "What documents are required?", language: "en" }));
  });

  it("shows an offline notice and pauses sending while the browser is offline", async () => {
    const user = userEvent.setup();
    renderWidget();
    const dialog = await openWidget(user);
    act(() => { Object.defineProperty(navigator, "onLine", { configurable: true, value: false }); window.dispatchEvent(new Event("offline")); });
    expect(within(dialog).getByRole("status")).toHaveTextContent("You're offline");
    await user.type(within(dialog).getByRole("textbox"), "documents");
    expect(within(dialog).getByRole("button", { name: "Send message" })).toBeDisabled();
    act(() => { Object.defineProperty(navigator, "onLine", { configurable: true, value: true }); window.dispatchEvent(new Event("online")); });
    expect(within(dialog).queryByText(/You're offline/)).not.toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Send message" })).toBeEnabled();
  });

  it("stays out of the way on the full-screen QR scanner", () => {
    renderWidget("/shop/scanner");
    expect(screen.queryByRole("button", { name: /open ration mitra ai assistant/i })).not.toBeInTheDocument();
  });
});
