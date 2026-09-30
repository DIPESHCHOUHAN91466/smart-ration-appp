import { Maximize2, Mic, Minimize2, Minus, RotateCcw, Search, X } from "lucide-react";
import ChatbotAvatar from "./ChatbotAvatar";
import ChatLanguageMenu from "./ChatLanguageMenu";
import { useChatbotStore } from "../../state/chatbotStore";
import { useTranslation } from "../../i18n/useTranslation";

export default function ChatbotHeader({ titleId, expanded, onToggleExpand, onMinimize, onClose, onClear, onToggleSearch, searching }) {
  const { t } = useTranslation();
  const requestVoice = useChatbotStore((s) => s.requestVoice);
  const action = (label, onClick, Icon, extra = {}) => (
    <button type="button" className="chat-head-btn" onClick={onClick} aria-label={label} title={label} {...extra}>
      <Icon size={17} aria-hidden="true" />
    </button>
  );

  return (
    <header className="chat-header">
      <div className="chat-identity">
        <div className="chat-avatar-wrap">
          <ChatbotAvatar size={42} />
          <span className="chat-online-dot" aria-hidden="true" />
        </div>
        <div>
          <h2 id={titleId}>{t("chat_title")}</h2>
          <p>{t("chat_subtitle")} · <span className="chat-online">{t("chat_status_online")}</span></p>
        </div>
      </div>
      <div className="chat-head-actions">
        {action(t("chat_search"), onToggleSearch, Search, { "aria-pressed": searching })}
        {action(t("chat_clear"), onClear, RotateCcw)}
        <span className="chat-desktop-only">{action(expanded ? t("chat_restore") : t("chat_expand"), onToggleExpand, expanded ? Minimize2 : Maximize2)}</span>
        {action(t("chat_minimize"), onMinimize, Minus)}
        {action(t("chat_close"), onClose, X)}
      </div>
      <div className="chat-quick-tools">
        <button type="button" className="chat-pill" onClick={requestVoice} title={t("voice_start")}>
          <Mic size={13} aria-hidden="true" /> {t("chat_menu_voice")}
        </button>
        <ChatLanguageMenu />
      </div>
    </header>
  );
}
