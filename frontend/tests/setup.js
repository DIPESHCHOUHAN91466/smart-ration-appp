import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import { useLanguageStore } from "../src/i18n/useTranslation";
import { useChatbotStore } from "../src/store/chatbotStore";

// jsdom lacks these browser APIs used by the UI.
Element.prototype.scrollTo = function scrollTo() {};
window.scrollTo = () => {};

afterEach(() => {
  cleanup();
  sessionStorage.clear();
  localStorage.clear();
  useLanguageStore.setState({ language: "en" });
  useChatbotStore.setState({ isOpen: false, pendingQuestion: null });
});
