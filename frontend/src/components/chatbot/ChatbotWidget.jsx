import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import ChatbotWindow from "./ChatbotWindow";
import ChatbotAvatar from "./ChatbotAvatar";
import { useChatbot } from "../../hooks/useChatbot";
import { useChatbotStore } from "../../state/chatbotStore";
import { useTranslation } from "../../i18n/useTranslation";
import "./chatbot.css";

// Routes where a floating button would sit on top of a full-screen tool.
const HIDDEN_ON = ["/shop/scanner"];

/**
 * The Public Help assistant: a floating launcher (bottom-right) and its chat window.
 * Mounted once in App; any page can open it with openChatbot(question) from store/chatbotStore.
 */
export default function ChatbotWidget() {
  const { t, language } = useTranslation();
  const location = useLocation();
  const isOpen = useChatbotStore((s) => s.isOpen);
  const openStore = useChatbotStore((s) => s.open);
  const closeStore = useChatbotStore((s) => s.close);
  const pendingQuestion = useChatbotStore((s) => s.pendingQuestion);
  const takePendingQuestion = useChatbotStore((s) => s.takePendingQuestion);

  const chat = useChatbot(language);
  const [expanded, setExpanded] = useState(false);
  const [unread, setUnread] = useState(() => (chat.messages.length ? 0 : 1)); // the welcome waiting
  const launcherRef = useRef(null);
  const inputRef = useRef(null);
  const openRef = useRef(isOpen);
  openRef.current = isOpen;

  // Count replies that arrive while the window is closed or minimized.
  chat.onBotMessage.current = () => {
    if (!openRef.current) setUnread((n) => n + 1);
  };

  const { loadWelcome, send } = chat;
  const hasMessages = chat.messages.length > 0;

  useEffect(() => {
    if (!isOpen) return;
    setUnread(0);
    if (!hasMessages) loadWelcome();
    const question = takePendingQuestion();
    if (question) send(question);
    const id = setTimeout(() => inputRef.current?.focus(), 60);
    return () => clearTimeout(id);
  }, [isOpen, pendingQuestion]); // eslint-disable-line react-hooks/exhaustive-deps

  // Switching language refreshes the quick buttons (their labels come from the server).
  useEffect(() => {
    if (isOpen && hasMessages) loadWelcome();
  }, [language]); // eslint-disable-line react-hooks/exhaustive-deps

  const close = useCallback(() => {
    closeStore();
    setExpanded(false);
    setTimeout(() => launcherRef.current?.focus(), 0);
  }, [closeStore]);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => e.key === "Escape" && close();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, close]);

  if (HIDDEN_ON.some((p) => location.pathname.startsWith(p))) return null;

  return (
    <div className="chatbot-root" data-open={isOpen || undefined}>
      {isOpen && (
        <ChatbotWindow
          chat={chat}
          expanded={expanded}
          inputRef={inputRef}
          onToggleExpand={() => setExpanded((e) => !e)}
          onMinimize={close}
          onClose={() => { close(); }}
        />
      )}

      {!isOpen && (
        <div className="chatbot-launcher-wrap">
          <span className="chatbot-tooltip" role="tooltip" id="chatbot-tooltip">{t("chat_tooltip")}</span>
          <button
            ref={launcherRef}
            type="button"
            className={`chatbot-launcher ${unread ? "has-unread" : ""}`}
            onClick={() => openStore()}
            aria-label={unread ? `${t("chat_open")} (${unread} ${t("chat_unread")})` : t("chat_open")}
            aria-describedby="chatbot-tooltip"
          >
            <ChatbotAvatar size={48} />
            {unread > 0 && <span className="chatbot-badge" aria-hidden="true">{unread > 9 ? "9+" : unread}</span>}
          </button>
        </div>
      )}
    </div>
  );
}
