import { useTranslation } from "../../i18n/useTranslation";

// Quick-question chips. Labels come from the server (already in the user's language);
// the topic id is what gets asked, so the answer is exact.
export default function ChatbotSuggestions({ suggestions, onChoose, disabled, compact = false }) {
  const { t } = useTranslation();
  if (!suggestions?.length) return null;
  return (
    <div className={`chat-suggestions ${compact ? "compact" : ""}`} role="group" aria-label={t("chat_quick_title")}>
      {!compact && <span className="chat-suggestions-title">{t("chat_quick_title")}</span>}
      <div className="chat-chips">
        {suggestions.map((s) => (
          <button type="button" key={s.topic} className="chat-chip" disabled={disabled} onClick={() => onChoose({ label: s.ask || s.label, topic: s.topic })}>
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
