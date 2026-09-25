import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { MessageText, toBlocks } from "../../src/components/chatbot/ChatbotMessage";

describe("reply formatting", () => {
  it("turns bullet and numbered lines into lists and keeps paragraphs", () => {
    expect(toBlocks("Intro\n• one\n• two\n\n1. first\n2. second\nOutro")).toEqual([
      { type: "p", text: "Intro" },
      { type: "ul", items: ["one", "two"] },
      { type: "gap" },
      { type: "ol", items: ["first", "second"] },
      { type: "p", text: "Outro" },
    ]);
  });

  it("drops leading and trailing blank lines", () => {
    expect(toBlocks("\n\nHello\n\n")).toEqual([{ type: "p", text: "Hello" }]);
  });

  it("renders Devanagari lists", () => {
    const { container } = render(<MessageText text={"कागदपत्रे:\n• आधार\n• पत्त्याचा पुरावा"} />);
    expect([...container.querySelectorAll("li")].map((li) => li.textContent)).toEqual(["आधार", "पत्त्याचा पुरावा"]);
  });

  it("never interprets markup", () => {
    const { container } = render(<MessageText text={"<b>bold</b>\n• <a href='https://x'>x</a>"} />);
    expect(container.querySelector("b, a")).toBeNull();
    expect(container.textContent).toContain("<b>bold</b>");
  });
});
