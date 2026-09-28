import { Globe2 } from "lucide-react";
import { LANGUAGE_OPTIONS } from "../i18n/translations";
import { useTranslation } from "../i18n/useTranslation";

// Same control as on Login and the dashboard, as a labelled component for public pages.
export default function LanguageSwitcher({ className = "" }) {
  const { t, language, setLanguage } = useTranslation();
  return (
    <label className={`lang-switch ${className}`.trim()}>
      <Globe2 size={15} aria-hidden="true" />
      <span className="sr-only">{t("language_label")}</span>
      <select value={language} onChange={(e) => setLanguage(e.target.value)} aria-label={t("language_label")}>
        {LANGUAGE_OPTIONS.map((opt) => (
          <option key={opt.code} value={opt.code} lang={opt.code}>{opt.label}</option>
        ))}
      </select>
    </label>
  );
}
