import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { MessageCircle, Mic } from "lucide-react";
import ChatbotWindow from "./ChatbotWindow";
import ChatbotAvatar from "./ChatbotAvatar";
import LanguageMenuItems from "./LanguageMenuItems";
import { useMenu } from "./useMenu";
import { useChatbot } from "../../hooks/useChatbot";
import { useChatbotStore } from "../../state/chatbotStore";
import { useTranslation } from "../../i18n/useTranslation";
import "./chatbot.css";

// Routes where a floating button would sit on top of a full-screen tool.
const HIDDEN_ON = ["/shop/scanner"];

// First-visit hint ("Need help? Ask Ration Mitra AI"): once per browser, shortly after load, briefly.
export const INTRO_SEEN_KEY = "rationMitraTooltipSeen";
const INTRO_DELAY_MS = 1500;
const INTRO_VISIBLE_MS = 5000;
const LONG_PRESS_MS = 500;

function readSeen() {
  try {
    return localStorage.getItem(INTRO_SEEN_KEY) === "true";
  } catch {
    return true; // storage blocked: don't risk showing it on every page
  }
}
function writeSeen() {
  try {
    localStorage.setItem(INTRO_SEEN_KEY, "true");
  } catch {
    // storage blocked
  }
}

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

  const requestVoice = useChatbotStore((s) => s.requestVoice);
  const chat = useChatbot(language);
  const menu = useMenu();
  const [intro, setIntro] = useState(false);
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

  // First visit only: show "Need help? Ask Ration Mitra AI" once, briefly, then never again (per browser).
  useEffect(() => {
    if (readSeen()) return undefined;
    const show = setTimeout(() => {
      if (openRef.current) return;
      setIntro(true);
      writeSeen();
    }, INTRO_DELAY_MS);
    const hide = setTimeout(() => setIntro(false), INTRO_DELAY_MS + INTRO_VISIBLE_MS);
    return () => {
      clearTimeout(show);
      clearTimeout(hide);
    };
  }, []);
  useEffect(() => {
    if (isOpen) {
      setIntro(false);
      menu.close(false);
    }
  }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---- launcher: click opens the chat; long-press / right-click / ↑ opens the assistant menu
  const longPressRef = useRef({ timer: null, fired: false });
  const setLauncherRef = useCallback(
    (node) => {
      launcherRef.current = node;
      menu.triggerRef.current = node;
    },
    [menu.triggerRef],
  );
  const openMenu = () => {
    setIntro(false);
    menu.setOpen(true);
  };
  const startLongPress = (e) => {
    if (e.button > 0) return; // primary button / touch only (some touch stacks report no button)
    longPressRef.current.fired = false;
    clearTimeout(longPressRef.current.timer);
    longPressRef.current.timer = setTimeout(() => {
      longPressRef.current.fired = true;
      openMenu();
    }, LONG_PRESS_MS);
  };
  const cancelLongPress = () => clearTimeout(longPressRef.current.timer);
  const onLauncherClick = () => {
    if (longPressRef.current.fired) {
      longPressRef.current.fired = false; // the long-press already opened the menu
      return;
    }
    menu.close(false);
    openStore();
  };

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
        <div className={`chatbot-launcher-wrap ${intro ? "intro" : ""} ${menu.open ? "menu-open" : ""}`.trim()}>
          <span className="chatbot-tooltip" role="tooltip" id="chatbot-tooltip">{t("chat_tooltip")}</span>
          <span className="sr-only" id="chatbot-launcher-hint">{t("chat_launcher_hint")}</span>
          <button
            ref={setLauncherRef}
            type="button"
            className={`chatbot-launcher ${unread ? "has-unread" : ""}`}
            onClick={onLauncherClick}
            onContextMenu={(e) => {
              e.preventDefault();
              openMenu();
            }}
            onPointerDown={startLongPress}
            onPointerUp={cancelLongPress}
            onPointerLeave={cancelLongPress}
            onPointerCancel={cancelLongPress}
            onKeyDown={(e) => {
              if (e.key === "ArrowUp" || e.key === "ContextMenu" || (e.key === "F10" && e.shiftKey)) {
                e.preventDefault();
                openMenu();
              }
            }}
            aria-label={unread ? `${t("chat_open")} (${unread} ${t("chat_unread")})` : t("chat_open")}
            title={t("chat_title")}
            aria-describedby="chatbot-tooltip chatbot-launcher-hint"
            aria-expanded={menu.open}
            aria-controls={menu.open ? "chatbot-assistant-menu" : undefined}
          >
            <ChatbotAvatar size={60} />
            {unread > 0 && <span className="chatbot-badge" aria-hidden="true">{unread > 9 ? "9+" : unread}</span>}
          </button>
          {menu.open && (
            <div
              ref={menu.menuRef}
              id="chatbot-assistant-menu"
              className="chat-menu launcher"
              role="menu"
              aria-label={t("chat_menu_options")}
              onKeyDown={menu.onMenuKeyDown}
            >
              <div className="chat-menu-title" aria-hidden="true">{t("chat_menu_title")}</div>
              <button type="button" role="menuitem" className="chat-menu-item" onClick={() => { menu.close(false); requestVoice(); }}>
                <Mic size={15} aria-hidden="true" /> {t("chat_menu_voice")}
              </button>
              <div className="chat-menu-sep" role="separator" />
              <LanguageMenuItems />
              <div className="chat-menu-sep" role="separator" />
              <button type="button" role="menuitem" className="chat-menu-item" onClick={() => { menu.close(false); openStore(); }}>
                <MessageCircle size={15} aria-hidden="true" /> {t("chat_menu_open")}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
