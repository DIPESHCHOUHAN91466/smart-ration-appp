import { ChevronDown, Globe2 } from "lucide-react";
import LanguageMenuItems from "./LanguageMenuItems";
import { useMenu } from "./useMenu";
import { LANGUAGE_OPTIONS } from "../../i18n/translations";
import { useTranslation } from "../../i18n/useTranslation";

// "🌐 English ▾" pill in the chat header: English / हिन्दी / मराठी (also the voice-recognition language).
export default function ChatLanguageMenu() {
  const { t, language } = useTranslation();
  const menu = useMenu();
  const current = LANGUAGE_OPTIONS.find((o) => o.code === language)?.label ?? "English";
  return (
    <span className="chat-menu-anchor">
      <button
        ref={menu.triggerRef}
        type="button"
        className="chat-pill"
        aria-label={`${t("chat_language")}: ${current}`}
        title={`${t("chat_language")}: ${current}`}
        aria-haspopup="menu"
        aria-expanded={menu.open}
        onClick={() => menu.setOpen((o) => !o)}
      >
        <Globe2 size={13} aria-hidden="true" /> <span lang={language}>{current}</span> <ChevronDown size={12} aria-hidden="true" />
      </button>
      {menu.open && (
        <div ref={menu.menuRef} className="chat-menu header" role="menu" aria-label={t("chat_language")} onKeyDown={menu.onMenuKeyDown}>
          <LanguageMenuItems onPicked={() => menu.close()} />
        </div>
      )}
    </span>
  );
}
