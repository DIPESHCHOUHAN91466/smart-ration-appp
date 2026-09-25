import { useEffect, useMemo, useRef, useState } from "react";
import { Search, X } from "lucide-react";
import ChatbotHeader from "./ChatbotHeader";
import ChatbotMessage from "./ChatbotMessage";
import ChatbotInput from "./ChatbotInput";
import ChatbotSuggestions from "./ChatbotSuggestions";
import ChatbotAvatar from "./ChatbotAvatar";
import { useTranslation } from "../../i18n/useTranslation";

export default function ChatbotWindow({ chat, expanded, onToggleExpand, onMinimize, onClose, inputRef }) {
  const { t } = useTranslation();
  const [searching, setSearching] = useState(false);
  const [query, setQuery] = useState("");
  const listRef = useRef(null);
  const searchRef = useRef(null);
  const titleId = "chatbot-title";

  const { messages, pending, suggestions } = chat;
  const needle = query.trim().toLowerCase();
  const visible = useMemo(
    () => (searching && needle ? messages.filter((m) => (m.text || "").toLowerCase().includes(needle)) : messages),
    [messages, searching, needle],
  );

  useEffect(() => {
    if (!searching) listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, pending, searching]);

  useEffect(() => {
    if (searching) searchRef.current?.focus();
  }, [searching]);

  const lastBot = [...messages].reverse().find((m) => m.role === "bot" && !m.error);
  const showQuick = !pending && !searching && (messages.length <= 1 || lastBot?.kind === "fallback");

  return (
    <section className={`chatbot-window ${expanded ? "expanded" : ""}`} role="dialog" aria-modal="false" aria-labelledby={titleId}>
      <ChatbotHeader
        titleId={titleId}
        expanded={expanded}
        searching={searching}
        onToggleExpand={onToggleExpand}
        onMinimize={onMinimize}
        onClose={onClose}
        onClear={() => { setSearching(false); setQuery(""); chat.clear(); }}
        onToggleSearch={() => { setSearching((s) => !s); setQuery(""); }}
      />

      {searching && (
        <div className="chat-search">
          <Search size={15} aria-hidden="true" />
          <input
            ref={searchRef}
            type="search"
            value={query}
            placeholder={t("chat_search_placeholder")}
            aria-label={t("chat_search")}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Escape" && (e.stopPropagation(), setSearching(false))}
          />
          <button type="button" onClick={() => { setSearching(false); setQuery(""); }} aria-label={t("chat_search_close")}>
            <X size={15} aria-hidden="true" />
          </button>
        </div>
      )}

      <div className="chat-messages" ref={listRef} role="log" aria-live="polite" aria-relevant="additions" aria-label={t("chat_messages_label")}>
        {messages.length === 0 && !pending && (
          <div className="chat-empty">
            <ChatbotAvatar size={64} />
            <h3>{t("chat_empty_title")}</h3>
            <p>{t("chat_empty_text")}</p>
          </div>
        )}
        {searching && needle && visible.length === 0 && <p className="chat-no-match">{t("chat_no_matches")}</p>}
        {visible.map((m) => (
          <ChatbotMessage
            key={m.id}
            message={m}
            highlight={searching && !!needle}
            onChoose={chat.choose}
            onRetry={chat.retry}
            onNavigate={onMinimize}
          />
        ))}
        {pending && (
          <div className="chat-row bot">
            <ChatbotAvatar size={28} />
            <div className="chat-bubble bot typing" role="status" aria-label={t("chat_typing")}>
              <span /><span /><span />
            </div>
          </div>
        )}
        {showQuick && <ChatbotSuggestions suggestions={suggestions} onChoose={chat.choose} disabled={pending} />}
      </div>

      {!showQuick && !searching && suggestions.length > 0 && (
        <ChatbotSuggestions suggestions={suggestions.slice(0, 4)} onChoose={chat.choose} disabled={pending} compact />
      )}
      <ChatbotInput ref={inputRef} onSend={chat.send} disabled={pending} />
      <p className="chat-disclaimer">{t("chat_disclaimer")}</p>
    </section>
  );
}
