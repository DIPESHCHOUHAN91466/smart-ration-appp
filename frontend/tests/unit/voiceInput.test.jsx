import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ChatbotInput from "../../src/components/chatbot/ChatbotInput";
import { mapRecognitionError, SPEECH_LANG } from "../../src/hooks/useSpeechRecognition";
import { useLanguageStore } from "../../src/i18n/useTranslation";

// A stand-in for the browser's SpeechRecognition: records what the hook asks for and lets the test emit
// results / errors / end exactly as a browser would.
class FakeRecognition {
  static instances = [];
  constructor() {
    this.started = false;
    this.stopped = false;
    this.aborted = false;
    FakeRecognition.instances.push(this);
  }
  start() { this.started = true; this.onstart?.(); } // real browsers fire onstart once capture begins
  stop() { this.stopped = true; this.onend?.(); }
  abort() { this.aborted = true; this.onend?.(); }
  // results: [[text, isFinal], ...] — the whole list so far, like event.results
  emit(results, resultIndex = 0) {
    const list = results.map(([text, isFinal]) => Object.assign([{ transcript: text }], { isFinal }));
    this.onresult?.({ resultIndex, results: list });
  }
  fail(code) { this.onerror?.({ error: code }); this.onend?.(); }
  static get last() { return FakeRecognition.instances.at(-1); }
}

function setup(props = {}) {
  const onSend = vi.fn();
  const ref = { current: null };
  const view = render(<ChatbotInput ref={ref} onSend={onSend} disabled={false} {...props} />);
  // The mic's label is translated, so find it by its role in the input box rather than by English text.
  return { onSend, unmount: view.unmount, box: screen.getByRole("textbox"), mic: () => view.container.querySelector("button.chat-mic") };
}

beforeEach(() => {
  FakeRecognition.instances = [];
  window.SpeechRecognition = FakeRecognition;
});
afterEach(() => {
  delete window.SpeechRecognition;
  delete window.webkitSpeechRecognition;
  useLanguageStore.setState({ language: "en" });
});

describe("voice input in the chatbot", () => {
  it("listens in the app language and shows recognised words live in the input", () => {
    const { box, mic } = setup();
    fireEvent.click(mic());
    const rec = FakeRecognition.last;
    expect(rec.started && rec.lang).toBe("en-IN");
    expect(rec.continuous && rec.interimResults).toBe(true);
    expect(screen.getByRole("status")).toHaveTextContent("Listening...");
    expect(mic()).toHaveAttribute("aria-label", "Stop voice input");
    expect(mic()).toHaveAttribute("aria-pressed", "true");

    act(() => rec.emit([["when will my", false]]));
    expect(box).toHaveValue("when will my");
    act(() => rec.emit([["when will my ration card come", true]]));
    expect(box).toHaveValue("when will my ration card come");
  });

  it("uses hi-IN and mr-IN for Hindi and Marathi, and keeps Devanagari text as spoken", () => {
    useLanguageStore.setState({ language: "hi" });
    const { box, mic } = setup();
    fireEvent.click(mic());
    expect(FakeRecognition.last.lang).toBe("hi-IN");
    act(() => FakeRecognition.last.emit([["मेरा राशन कार्ड कब तक आएगा?", true]]));
    expect(box).toHaveValue("मेरा राशन कार्ड कब तक आएगा?");
    expect(SPEECH_LANG.mr).toBe("mr-IN");
  });

  it("switching the app language ends the session; the next one uses the new language", () => {
    const { mic } = setup();
    fireEvent.click(mic());
    const first = FakeRecognition.last;
    act(() => useLanguageStore.setState({ language: "mr" }));
    expect(first.stopped).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "व्हॉइस इनपुट सुरू करा" }));
    expect(FakeRecognition.last.lang).toBe("mr-IN");
  });

  it("never sends automatically: stop keeps the text, the user edits and sends it", () => {
    const { box, mic, onSend } = setup();
    fireEvent.change(box, { target: { value: "Hello" } });
    fireEvent.click(mic());
    act(() => FakeRecognition.last.emit([["what documents are needed", true]]));
    expect(box).toHaveValue("Hello what documents are needed"); // appended to what was typed
    fireEvent.click(mic()); // stop
    expect(FakeRecognition.last.stopped).toBe(true);
    expect(onSend).not.toHaveBeenCalled();
    expect(box).toHaveValue("Hello what documents are needed");
    fireEvent.change(box, { target: { value: "Hello, what documents are needed?" } });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    expect(onSend).toHaveBeenCalledWith("Hello, what documents are needed?");
    expect(box).toHaveValue("");
  });

  it("sending while listening stops recognition and a late result cannot refill the box", () => {
    const { box, mic, onSend } = setup();
    fireEvent.click(mic());
    const rec = FakeRecognition.last;
    act(() => rec.emit([["eligibility", false]]));
    fireEvent.keyDown(box, { key: "Enter" });
    expect(onSend).toHaveBeenCalledWith("eligibility");
    expect(rec.aborted).toBe(true);
    act(() => rec.emit([["eligibility rules", true]])); // arrives after abort: ignored
    expect(box).toHaveValue("");
  });

  it("cancel (button or Esc) discards the spoken text and restores what was typed", () => {
    const { box, mic } = setup();
    fireEvent.change(box, { target: { value: "typed" } });
    fireEvent.click(mic());
    act(() => FakeRecognition.last.emit([["spoken words", false]]));
    fireEvent.click(screen.getByRole("button", { name: /Cancel/ }));
    expect(box).toHaveValue("typed");
    expect(FakeRecognition.last.aborted).toBe(true);

    fireEvent.click(mic());
    act(() => FakeRecognition.last.emit([["more words", false]]));
    fireEvent.keyDown(box, { key: "Escape" });
    expect(box).toHaveValue("typed");
    expect(screen.queryByRole("status")).toBeNull();
  });

  it.each([
    ["not-allowed", "Microphone permission was denied. Please allow microphone access in your browser settings."],
    ["audio-capture", "No microphone was found. Please connect a microphone and try again."],
    ["no-speech", "I couldn't hear anything. Please try again."],
    ["network", "Voice recognition is temporarily unavailable. Please try again."],
    ["language-not-supported", "Voice input is not supported for this language on your current browser."],
  ])("shows a friendly message for %s", (code, message) => {
    const { mic } = setup();
    fireEvent.click(mic());
    act(() => FakeRecognition.last.fail(code));
    expect(screen.getByRole("alert")).toHaveTextContent(message);
    expect(mic()).toHaveAttribute("aria-label", "Start voice input"); // back to the normal mic
  });

  it("explains when the browser has no speech recognition", () => {
    delete window.SpeechRecognition;
    const { mic } = setup();
    fireEvent.click(mic());
    expect(screen.getByRole("alert")).toHaveTextContent("Voice input isn't supported in this browser. Please use Chrome or another supported browser.");
  });

  it("caps long dictation at the chat's 500-character limit", () => {
    const { box, mic } = setup();
    fireEvent.click(mic());
    act(() => FakeRecognition.last.emit([["word ".repeat(200), true]]));
    expect(box.value.length).toBe(500);
  });

  it("releases the microphone when the chat is closed mid-sentence", () => {
    const { mic, unmount } = setup();
    fireEvent.click(mic());
    const rec = FakeRecognition.last;
    unmount();
    expect(rec.aborted).toBe(true);
  });

  it("maps every browser error code to a message or to a silent cancel", () => {
    expect(mapRecognitionError("service-not-allowed")).toBe("denied");
    expect(mapRecognitionError("aborted")).toBeNull();
    expect(mapRecognitionError("something-new")).toBe("failed");
  });
});
