import { forwardRef, useState } from "react";
import { SendHorizontal, ShieldCheck } from "lucide-react";
import { useTranslation } from "../../i18n/useTranslation";

export const MAX_LENGTH = 500;

// Enter sends, Shift+Enter adds a line. The server enforces the same limit.
const ChatbotInput = forwardRef(function ChatbotInput({ onSend, disabled }, ref) {
  const { t } = useTranslation();
  const [value, setValue] = useState("");
  const left = MAX_LENGTH - value.length;

  const submit = (event) => {
    event?.preventDefault();
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
  };

  return (
    <form className="chat-input" onSubmit={submit}>
      <div className="chat-input-box">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          maxLength={MAX_LENGTH}
          placeholder={t("chat_placeholder")}
          aria-label={t("chat_placeholder")}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) submit(e);
          }}
        />
        <button type="submit" className="chat-send" disabled={disabled || !value.trim()} aria-label={t("chat_send")} title={t("chat_send")}>
          <SendHorizontal size={18} aria-hidden="true" />
        </button>
      </div>
      <div className="chat-input-meta">
        <span><ShieldCheck size={12} aria-hidden="true" /> {t("chat_privacy")}</span>
        {left <= 80 && <span className={left <= 20 ? "warn" : ""} aria-live="polite">{left} {t("chat_chars_left")}</span>}
      </div>
    </form>
  );
});

export default ChatbotInput;
