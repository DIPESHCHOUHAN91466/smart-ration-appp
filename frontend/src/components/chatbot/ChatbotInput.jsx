import { forwardRef, useEffect, useRef, useState } from "react";
import { Mic, SendHorizontal, ShieldCheck, Square, X } from "lucide-react";
import { useTranslation } from "../../i18n/useTranslation";
import { SPEECH_LANG, VOICE_ERROR, VOICE_STATUS, useSpeechRecognition } from "../../hooks/useSpeechRecognition";
import { useChatbotStore } from "../../state/chatbotStore";

export const MAX_LENGTH = 500;

const VOICE_ERROR_KEY = {
  [VOICE_ERROR.UNSUPPORTED]: "voice_err_unsupported",
  [VOICE_ERROR.DENIED]: "voice_err_denied",
  [VOICE_ERROR.NO_MIC]: "voice_err_no_mic",
  [VOICE_ERROR.NO_SPEECH]: "voice_err_no_speech",
  [VOICE_ERROR.NETWORK]: "voice_err_network",
  [VOICE_ERROR.LANGUAGE]: "voice_err_language",
  [VOICE_ERROR.FAILED]: "voice_err_network",
};

// Enter sends, Shift+Enter adds a line. The server enforces the same limit.
// Voice input (🎤) fills this same box with recognised text — it is never sent automatically: the user
// can keep speaking, stop, edit and then send as usual, or cancel to restore what was typed before.
const ChatbotInput = forwardRef(function ChatbotInput({ onSend, disabled }, ref) {
  const { t, language } = useTranslation();
  const [value, setValue] = useState("");
  const baseRef = useRef(""); // what was typed before the current voice session
  const voice = useSpeechRecognition({
    lang: SPEECH_LANG[language] ?? SPEECH_LANG.en,
    onTranscript: (text) => {
      const base = baseRef.current.trimEnd();
      setValue(`${base}${base && text ? " " : ""}${text}`.slice(0, MAX_LENGTH));
    },
  });
  const left = MAX_LENGTH - value.length;

  // Voice requested from the header 🎤 or the launcher menu: start listening here (the only voice code).
  const pendingVoice = useChatbotStore((s) => s.pendingVoice);
  const consumeVoice = useChatbotStore((s) => s.consumeVoice);
  const { startListening, isListening } = voice;
  useEffect(() => {
    if (!pendingVoice || disabled) return;
    consumeVoice();
    if (!isListening) {
      baseRef.current = value;
      startListening();
    }
  }, [pendingVoice, disabled]); // eslint-disable-line react-hooks/exhaustive-deps

  const submit = (event) => {
    event?.preventDefault();
    if (!value.trim() || disabled) return;
    // Stop listening without letting a late result refill the box after it is cleared.
    if (voice.isListening) voice.cancelListening();
    onSend(value);
    setValue("");
  };

  const toggleVoice = () => {
    if (voice.isListening) {
      voice.stopListening(); // keeps the recognised text for editing
      return;
    }
    baseRef.current = value;
    voice.startListening();
  };

  const cancelVoice = () => {
    voice.cancelListening();
    setValue(baseRef.current);
    ref?.current?.focus();
  };

  const errorKey = voice.error ? VOICE_ERROR_KEY[voice.error] : null;

  return (
    <form className="chat-input" onSubmit={submit}>
      <div className={`chat-input-box ${voice.isListening ? "listening" : ""}`}>
        <textarea
          ref={ref}
          rows={1}
          value={value}
          maxLength={MAX_LENGTH}
          placeholder={voice.isListening ? t("voice_listening") : t("chat_placeholder")}
          aria-label={t("chat_placeholder")}
          onChange={(e) => {
            setValue(e.target.value);
            if (voice.error) voice.clearError();
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape" && voice.isListening) {
              e.preventDefault();
              e.stopPropagation(); // Esc cancels voice input here, it does not close the chat
              cancelVoice();
              return;
            }
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) submit(e);
          }}
        />
        <button
          type="button"
          className={`chat-mic ${voice.isListening ? "listening" : ""} ${voice.supported ? "" : "unsupported"}`.trim()}
          onClick={toggleVoice}
          disabled={disabled}
          aria-pressed={voice.isListening}
          aria-label={voice.isListening ? t("voice_stop") : t("voice_start")}
          title={voice.isListening ? t("voice_stop") : t("voice_tooltip")}
        >
          {voice.isListening ? <Square size={14} fill="currentColor" aria-hidden="true" /> : <Mic size={18} aria-hidden="true" />}
        </button>
        <button type="submit" className="chat-send" disabled={disabled || !value.trim()} aria-label={t("chat_send")} title={t("chat_send")}>
          <SendHorizontal size={18} aria-hidden="true" />
        </button>
      </div>

      {voice.isListening && (
        <div className="chat-voice-status" role="status" aria-live="polite">
          <span className="chat-voice-dot" aria-hidden="true" />
          <span>
            {voice.status === VOICE_STATUS.REQUESTING_PERMISSION
              ? t("voice_requesting")
              : voice.status === VOICE_STATUS.PROCESSING
                ? t("voice_processing")
                : t("voice_listening")}
          </span>
          <button type="button" className="chat-voice-cancel" onClick={cancelVoice}>
            <X size={13} aria-hidden="true" /> {t("voice_cancel")}
          </button>
        </div>
      )}
      {!voice.isListening && errorKey && (
        <div className="chat-voice-status error" role="alert">
          <span>{t(errorKey)}</span>
          <button type="button" className="chat-voice-cancel" onClick={voice.clearError} aria-label={t("voice_dismiss")}>
            <X size={13} aria-hidden="true" />
          </button>
        </div>
      )}

      <div className="chat-input-meta">
        <span><ShieldCheck size={12} aria-hidden="true" /> {t("chat_privacy")}</span>
        {left <= 80 && <span className={left <= 20 ? "warn" : ""} aria-live="polite">{left} {t("chat_chars_left")}</span>}
      </div>
    </form>
  );
});

export default ChatbotInput;
