import { Check } from "lucide-react";
import { LANGUAGE_OPTIONS } from "../../i18n/translations";
import { useTranslation } from "../../i18n/useTranslation";

// English / हिन्दी / मराठी as menu radio items. The choice is the app-wide language (persisted by
// useLanguageStore), so the chat, the rest of the app and voice recognition all switch together.
export default function LanguageMenuItems({ onPicked }) {
  const { language, setLanguage } = useTranslation();
  return LANGUAGE_OPTIONS.map((opt) => (
    <button
      key={opt.code}
      type="button"
      role="menuitemradio"
      aria-checked={language === opt.code}
      lang={opt.code}
      className="chat-menu-item"
      onClick={() => {
        setLanguage(opt.code);
        onPicked?.(opt.code);
      }}
    >
      <span className="chat-menu-check" aria-hidden="true">{language === opt.code && <Check size={14} />}</span>
      {opt.label}
    </button>
  ));
}
